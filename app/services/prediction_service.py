import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from app.services.supabase_service import insert_prediction, get_predictions
from app.services.data_service import fetch_from_yfinance, fetch_from_coingecko, merge_and_clean, add_technical_indicators
from app.models import model_manager
from app.core.logger import get_logger

logger = get_logger("prediction_service")


def generate_predictions() -> dict:
    """
    Run the full prediction pipeline:
      1. Fetch the last 90 days of BTC data (enough for 60-day LSTM + indicator warmup).
      2. Compute all technical indicators.
      3. Run Prophet, LSTM, and RF via model_manager.
      4. Persist each model's prediction to the Supabase predictions table.
      5. Return a consolidated dict of all predictions.
    """
    # 1. Fetch recent data for inference
    logger.info("Fetching latest market data for prediction inference...")
    end_date   = datetime.now()
    start_date = end_date - timedelta(days=90)

    try:
        raw_df = fetch_from_yfinance(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    except Exception as yf_err:
        logger.warning(f"yfinance failed: {yf_err}. Using CoinGecko fallback...")
        raw_df = fetch_from_coingecko(days=90)

    df_cleaned = merge_and_clean(raw_df)
    df         = add_technical_indicators(df_cleaned)

    # 2. Ensure models are loaded (no-op if already in memory from startup)
    model_manager.load_all_models()

    # 3. Run all models via model_manager
    pred = model_manager.run_all_predictions(df)

    prediction_date = pred.get("prediction_date")
    prophet_price   = pred.get("prophet_next")
    lstm_price      = pred.get("lstm_next")
    rf_price        = pred.get("rf_next")
    rf_direction    = pred.get("rf_direction")
    ensemble_price  = pred.get("ensemble_next")

    logger.info(f"Prediction Date: {prediction_date}")
    logger.info(f"  Prophet:  {f'${prophet_price:,.2f}' if prophet_price else 'N/A'}")
    logger.info(f"  LSTM:     {f'${lstm_price:,.2f}' if lstm_price else 'N/A'}")
    logger.info(f"  RF:       {f'${rf_price:,.2f}' if rf_price else 'N/A'} ({rf_direction})")
    logger.info(f"  Ensemble: {f'${ensemble_price:,.2f}' if ensemble_price else 'N/A'}")

    # 4. Save each model's prediction to Supabase
    saved = 0
    predictions_to_save = []

    if prophet_price is not None:
        predictions_to_save.append({
            "model_used": "prophet",
            "prediction_type": "price_forecast_7d",
            "predicted_value": round(prophet_price, 2),
            "prediction_date": str(prediction_date),
            "confidence_score": 0.75
        })

    if lstm_price is not None:
        predictions_to_save.append({
            "model_used": "lstm",
            "prediction_type": "price_forecast_1d",
            "predicted_value": round(lstm_price, 2),
            "prediction_date": str(prediction_date),
            "confidence_score": 0.82
        })

    if rf_price is not None:
        predictions_to_save.append({
            "model_used": "random_forest",
            "prediction_type": "price_forecast_1d",
            "predicted_value": round(rf_price, 2),
            "prediction_date": str(prediction_date),
            "confidence_score": 0.78
        })

    if ensemble_price is not None:
        predictions_to_save.append({
            "model_used": "ensemble",
            "prediction_type": "price_forecast_1d",
            "predicted_value": round(ensemble_price, 2),
            "prediction_date": str(prediction_date),
            "confidence_score": 0.90
        })

    for record in predictions_to_save:
        res = insert_prediction(record)
        if res.get("status") == "success":
            saved += 1

    logger.info(f"Saved {saved}/{len(predictions_to_save)} prediction records to Supabase.")

    return {
        "prediction_date":  prediction_date,
        "prophet_price":    prophet_price,
        "lstm_price":       lstm_price,
        "rf_price":         rf_price,
        "rf_direction":     rf_direction,
        "ensemble_price":   ensemble_price,
        "saved_count":      saved
    }


if __name__ == "__main__":
    result = generate_predictions()
    print(result)
