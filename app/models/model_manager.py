"""
model_manager.py — Central orchestration layer for all 3 ML models.

Responsibilities:
  - load_all_models()          : Load all trained models from disk into memory.
  - run_all_predictions(df)    : Run all 3 models and return a combined prediction dict.
  - retrain_all_models(df)     : Retrain all 3 models, save artifacts, and log metrics to Supabase.
  - get_ensemble_prediction()  : Compute weighted average price from RF + LSTM (Prophet handles trend).
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from app.core.logger import get_logger
from app.services.supabase_service import insert_model_metrics

import app.models.prophet_model as prophet_module
import app.models.lstm_model    as lstm_module
import app.models.rf_model      as rf_module

logger = get_logger("model_manager")

# ─── In-Memory Model Store ─────────────────────────────────────────────────────
_store = {
    "prophet":    None,  # Fitted Prophet model
    "lstm":       None,  # Keras LSTM model
    "lstm_scaler": None, # MinMaxScaler for LSTM
    "rf_reg":     None,  # RandomForestRegressor
    "rf_clf":     None,  # RandomForestClassifier
    "rf_features": None, # List[str] of feature columns RF was trained on
}

# Ensemble weights: RF regressor is slightly preferred over LSTM due to lower variance
ENSEMBLE_WEIGHTS = {
    "lstm": 0.40,
    "rf":   0.60,
}


def load_all_models() -> dict:
    """
    Load all trained model artifacts from disk into the in-memory store.
    Call this at application startup before running predictions.

    Returns:
        Dict summarising which models loaded successfully.
    """
    status = {}

    # 1. Prophet
    try:
        _store["prophet"] = prophet_module.load_model()
        status["prophet"] = "loaded"
    except FileNotFoundError as e:
        logger.warning(f"Prophet model not found — {e}")
        status["prophet"] = "missing"
    except Exception as e:
        logger.error(f"Prophet load error: {e}")
        status["prophet"] = "error"

    # 2. LSTM
    try:
        _store["lstm"], _store["lstm_scaler"] = lstm_module.load_model()
        status["lstm"] = "loaded"
    except FileNotFoundError as e:
        logger.warning(f"LSTM model not found — {e}")
        status["lstm"] = "missing"
    except Exception as e:
        logger.error(f"LSTM load error: {e}")
        status["lstm"] = "error"

    # 3. Random Forest (Regressor + Classifier)
    try:
        _store["rf_reg"], _store["rf_features"] = rf_module.load_regressor()
        _store["rf_clf"] = rf_module.load_classifier()
        status["random_forest"] = "loaded"
    except FileNotFoundError as e:
        logger.warning(f"RF models not found — {e}")
        status["random_forest"] = "missing"
    except Exception as e:
        logger.error(f"RF load error: {e}")
        status["random_forest"] = "error"

    loaded_count = sum(1 for v in status.values() if v == "loaded")
    logger.info(f"Model Manager: {loaded_count}/{len(status)} models loaded successfully. Status: {status}")
    return status


def run_all_predictions(df: pd.DataFrame) -> dict:
    """
    Run all 3 models against the provided DataFrame and return a unified prediction dict.

    Args:
        df: DataFrame with technical indicators (output of add_technical_indicators).
            Must be sorted by date ascending.

    Returns:
        Dict with keys:
          - prophet_7day  : pd.DataFrame  — 7-day forecast (date, yhat, yhat_lower, yhat_upper)
          - prophet_next  : float         — Tomorrow's Prophet price
          - lstm_next     : float         — Tomorrow's LSTM price
          - rf_next       : float         — Tomorrow's RF price
          - rf_direction  : str           — 'UP' or 'DOWN'
          - ensemble_next : float         — Weighted RF + LSTM average
          - prediction_date : date        — Target prediction date
    """
    results = {}

    # Infer prediction target date from the latest date in the dataset
    latest_date = pd.to_datetime(df["date"].max()).date()
    prediction_date = latest_date + timedelta(days=1)
    results["prediction_date"] = prediction_date

    # 1. Prophet — 7-day forecast
    prophet_next = None
    if _store["prophet"] is not None:
        try:
            forecast_df = prophet_module.predict_next_7_days(_store["prophet"])
            results["prophet_7day"] = forecast_df
            results["prophet_next"] = float(forecast_df.iloc[0]["yhat"])
            prophet_next = results["prophet_next"]
        except Exception as e:
            logger.error(f"Prophet prediction failed: {e}")
            results["prophet_7day"] = pd.DataFrame()
            results["prophet_next"] = None
    else:
        logger.warning("Prophet model not loaded. Skipping Prophet prediction.")
        results["prophet_7day"] = pd.DataFrame()
        results["prophet_next"] = None

    # 2. LSTM — next-day price
    lstm_next = None
    if _store["lstm"] is not None and _store["lstm_scaler"] is not None:
        try:
            lstm_next = lstm_module.predict_next_day(_store["lstm"], _store["lstm_scaler"], df)
            results["lstm_next"] = lstm_next
        except Exception as e:
            logger.error(f"LSTM prediction failed: {e}")
            results["lstm_next"] = None
    else:
        logger.warning("LSTM model not loaded. Skipping LSTM prediction.")
        results["lstm_next"] = None

    # 3. Random Forest — next-day price + direction
    rf_next = None
    if _store["rf_reg"] is not None and _store["rf_clf"] is not None:
        try:
            latest_row = df.sort_values("date").iloc[-1:].copy()
            rf_result  = rf_module.predict_next_day(
                _store["rf_reg"],
                _store["rf_clf"],
                latest_row,
                _store["rf_features"]
            )
            rf_next = rf_result["predicted_price"]
            results["rf_next"]      = rf_next
            results["rf_direction"] = rf_result["direction_label"]
        except Exception as e:
            logger.error(f"Random Forest prediction failed: {e}")
            results["rf_next"]      = None
            results["rf_direction"] = None
    else:
        logger.warning("RF models not loaded. Skipping RF prediction.")
        results["rf_next"]      = None
        results["rf_direction"] = None

    # 4. Ensemble — weighted average of LSTM + RF (Prophet excluded since it's for trend)
    ensemble_next = get_ensemble_prediction(lstm_price=lstm_next, rf_price=rf_next)
    results["ensemble_next"] = ensemble_next

    logger.info(f"All predictions for {prediction_date}: "
                f"Prophet={prophet_next}, LSTM={lstm_next}, RF={rf_next}, Ensemble={ensemble_next}")
    return results


def retrain_all_models(df: pd.DataFrame) -> dict:
    """
    Retrain all 3 models from scratch, save their artifacts, and log evaluation
    metrics to the Supabase model_metrics table.

    Args:
        df: Full historical DataFrame with technical indicators.

    Returns:
        Dict summarising which models were retrained and their evaluation metrics.
    """
    logger.info("=" * 60)
    logger.info("STARTING FULL MODEL RETRAINING PIPELINE")
    logger.info("=" * 60)
    report = {}

    # 1. Prophet
    try:
        logger.info("Retraining Prophet...")
        model  = prophet_module.train(df)
        metrics = prophet_module.evaluate(model, df)
        _store["prophet"] = model
        report["prophet"] = {"status": "retrained", "metrics": metrics}

        insert_model_metrics({
            "model_name": "prophet",
            "mae":  metrics.get("mae", 0),
            "rmse": metrics.get("rmse", 0),
            "mape": metrics.get("mape", 0),
            "r2":   0.0  # Prophet does not produce R2
        })
    except Exception as e:
        logger.error(f"Prophet retraining failed: {e}")
        report["prophet"] = {"status": "failed", "error": str(e)}

    # 2. LSTM
    try:
        logger.info("Retraining LSTM (this may take several minutes on CPU)...")
        model, scaler = lstm_module.train(df)
        metrics       = lstm_module.evaluate(model, scaler, df)
        _store["lstm"]        = model
        _store["lstm_scaler"] = scaler
        report["lstm"] = {"status": "retrained", "metrics": metrics}

        insert_model_metrics({
            "model_name": "lstm",
            "mae":  metrics.get("mae", 0),
            "rmse": metrics.get("rmse", 0),
            "mape": 0.0,  # LSTM evaluation does not produce MAPE
            "r2":   0.0
        })
    except Exception as e:
        logger.error(f"LSTM retraining failed: {e}")
        report["lstm"] = {"status": "failed", "error": str(e)}

    # 3. Random Forest
    try:
        logger.info("Retraining Random Forest...")
        reg_model = rf_module.train_regressor(df)
        clf_model = rf_module.train_classifier(df)
        # Load features list saved during training
        _, feature_cols = rf_module.load_regressor()
        metrics = rf_module.evaluate(reg_model, clf_model, df)

        _store["rf_reg"]      = reg_model
        _store["rf_clf"]      = clf_model
        _store["rf_features"] = feature_cols
        report["random_forest"] = {"status": "retrained", "metrics": metrics}

        insert_model_metrics({
            "model_name": "random_forest",
            "mae":  metrics.get("mae", 0),
            "rmse": metrics.get("rmse", 0),
            "mape": metrics.get("mape", 0),
            "r2":   metrics.get("r2", 0)
        })
    except Exception as e:
        logger.error(f"RF retraining failed: {e}")
        report["random_forest"] = {"status": "failed", "error": str(e)}

    logger.info("=" * 60)
    logger.info(f"RETRAINING COMPLETE: {report}")
    logger.info("=" * 60)
    return report


def get_ensemble_prediction(lstm_price: float = None, rf_price: float = None) -> float:
    """
    Compute a weighted average of the RF Regressor and LSTM next-day price predictions.
    Prophet is intentionally excluded from the ensemble as it is better suited for trend
    direction (7-day outlook) rather than precise next-day price prediction.

    Args:
        lstm_price: Predicted price from LSTM (or None if unavailable).
        rf_price:   Predicted price from Random Forest (or None if unavailable).

    Returns:
        Weighted average price as a float, or None if both inputs are None.
    """
    available = {}
    if lstm_price is not None:
        available["lstm"] = lstm_price
    if rf_price is not None:
        available["rf"] = rf_price

    if not available:
        logger.warning("No model predictions available for ensemble calculation.")
        return None

    # Adjust weights if only one model is available
    if len(available) == 1:
        result = list(available.values())[0]
        logger.info(f"Only one model available for ensemble. Returning raw price: ${result:,.2f}")
        return result

    # Weighted average using ENSEMBLE_WEIGHTS
    total_weight = sum(ENSEMBLE_WEIGHTS[k] for k in available)
    ensemble = sum(ENSEMBLE_WEIGHTS[k] * v for k, v in available.items()) / total_weight

    logger.info(f"Ensemble Prediction — LSTM: ${lstm_price:,.2f}, RF: ${rf_price:,.2f} → Ensemble: ${ensemble:,.2f}")
    return round(ensemble, 2)
