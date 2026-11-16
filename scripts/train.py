import os
import sys
from datetime import datetime, timedelta

# Ensure root-level app package is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.supabase_service import get_historical_data
from app.services.data_service import (
    fetch_from_yfinance, fetch_from_coingecko,
    merge_and_clean, add_technical_indicators
)
from app.models import prophet_model, lstm_model, rf_model
from app.core.logger import get_logger

logger = get_logger("train_pipeline")


def load_training_data() -> "pd.DataFrame":
    """
    Load training data — preferring Supabase, falling back to live API fetch.
    Returns a DataFrame with technical indicators applied.
    """
    import pandas as pd

    logger.info("Attempting to load training data from Supabase...")
    try:
        df_db = get_historical_data(days=1095)  # ~3 years
        if not df_db.empty and len(df_db) > 200:
            logger.info(f"Loaded {len(df_db)} records from Supabase.")
            return add_technical_indicators(df_db)
    except Exception as e:
        logger.error(f"Supabase load failed: {e}")

    logger.info("Falling back to live API fetch...")
    end_date   = datetime.now()
    start_date = end_date - timedelta(days=3 * 365)

    try:
        raw_df = fetch_from_yfinance(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    except Exception as e:
        logger.warning(f"yfinance failed: {e}. Trying CoinGecko...")
        raw_df = fetch_from_coingecko(days=1095)

    df_cleaned    = merge_and_clean(raw_df)
    df_indicators = add_technical_indicators(df_cleaned)
    logger.info(f"API fallback successful: {len(df_indicators)} rows with indicators.")
    return df_indicators


def main():
    logger.info("=" * 65)
    logger.info("  BITCOIN PREDICTION MODEL TRAINING PIPELINE")
    logger.info("=" * 65)

    # Step 1 — Load data
    df = load_training_data()
    logger.info(f"Training data ready: {len(df)} rows, columns: {list(df.columns)}")

    results = {}

    # Step 2 — Train Prophet
    logger.info("\n[1/3] Training Prophet Model...")
    try:
        p_model  = prophet_model.train(df)
        prophet_model.save_model(p_model)
        p_metrics = prophet_model.evaluate(p_model, df)
        logger.info(f"    ✅ Prophet — MAE: ${p_metrics['mae']:,.2f}, RMSE: ${p_metrics['rmse']:,.2f}, MAPE: {p_metrics['mape']:.4f}%")
        results["prophet"] = p_metrics
    except Exception as e:
        logger.error(f"    ❌ Prophet training failed: {e}")
        results["prophet"] = {"error": str(e)}

    # Step 3 — Train LSTM
    logger.info("\n[2/3] Training LSTM Model (CPU — may take several minutes)...")
    try:
        l_model, l_scaler = lstm_model.train(df, epochs=50, batch_size=32)
        l_metrics = lstm_model.evaluate(l_model, l_scaler, df)
        logger.info(f"    ✅ LSTM — MAE: ${l_metrics['mae']:,.2f}, RMSE: ${l_metrics['rmse']:,.2f}")
        results["lstm"] = l_metrics
    except Exception as e:
        logger.error(f"    ❌ LSTM training failed: {e}")
        results["lstm"] = {"error": str(e)}

    # Step 4 — Train Random Forest
    logger.info("\n[3/3] Training Random Forest Regressor + Classifier...")
    try:
        rf_reg = rf_model.train_regressor(df)
        rf_clf = rf_model.train_classifier(df)
        rf_metrics = rf_model.evaluate(rf_reg, rf_clf, df)
        logger.info(f"    ✅ RF — MAE: ${rf_metrics['mae']:,.2f}, RMSE: ${rf_metrics['rmse']:,.2f}, "
                    f"R2: {rf_metrics['r2']:.4f}, Accuracy: {rf_metrics['accuracy']:.2f}%")
        results["random_forest"] = rf_metrics
    except Exception as e:
        logger.error(f"    ❌ Random Forest training failed: {e}")
        results["random_forest"] = {"error": str(e)}

    # Summary
    logger.info("\n" + "=" * 65)
    logger.info("  TRAINING COMPLETE — SUMMARY")
    logger.info("=" * 65)
    for model_name, metrics in results.items():
        if "error" in metrics:
            logger.info(f"  {model_name:<20} : ❌ FAILED — {metrics['error']}")
        else:
            logger.info(f"  {model_name:<20} : ✅ SUCCESS — {metrics}")
    logger.info("=" * 65)
    logger.info("Models saved to: data/saved_models/")


if __name__ == "__main__":
    main()
