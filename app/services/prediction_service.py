import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from app.services.supabase_service import insert_prediction
from app.services.data_service import fetch_from_yfinance, fetch_from_coingecko, merge_and_clean, add_technical_indicators
from app.models.prophet_model import ProphetModelWrapper
from app.models.lstm_model import LSTMModelWrapper
from app.models.regressor_model import RegressorModelWrapper
from app.core.logger import get_logger

logger = get_logger("prediction_service")

def generate_predictions() -> dict:
    """
    Generate predictions for the next trading day and 7-day trend using Prophet, LSTM, and Random Forest.
    Saves predictions into Supabase predictions table under the new schema structure.
    """
    # 1. Fetch latest data for inference (retrieve last 60 days to have enough window for indicators + lookback)
    logger.info("Fetching latest data for inference...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)
    
    try:
        raw_df = fetch_from_yfinance(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    except Exception as yf_err:
        logger.warning(f"yfinance failed for inference fetch: {yf_err}. Using CoinGecko fallback...")
        raw_df = fetch_from_coingecko(days=60)
        
    df_cleaned = merge_and_clean(raw_df)
    df = add_technical_indicators(df_cleaned)
    
    # Get latest date in our df
    latest_row = df.sort_values('date').iloc[-1]
    latest_date = latest_row['date']
    latest_close = float(latest_row['close'])
    
    prediction_target_date = latest_date + timedelta(days=1)
    logger.info(f"Latest data point: {latest_date} (Close: ${latest_close:,.2f})")
    logger.info(f"Generating prediction for date: {prediction_target_date}")
    
    # 2. Load models and predict
    # Prophet Prediction
    prophet_wrapper = ProphetModelWrapper()
    prophet_forecast = prophet_wrapper.predict_next_days(days=7)
    prophet_next_day = float(prophet_forecast[0]) # Next day
    prophet_7th_day = float(prophet_forecast[6]) # 7th day
    
    # LSTM Prediction
    lstm_wrapper = LSTMModelWrapper(lookback=30)
    # Get recent prices for LSTM input (at least 30 values)
    recent_prices = df.sort_values('date')['close'].values
    lstm_next_day = float(lstm_wrapper.predict_next_day(recent_prices))
    
    # Scikit-learn Regressor Prediction
    sklearn_wrapper = RegressorModelWrapper()
    sklearn_next_day = float(sklearn_wrapper.predict_next_day(df))
    
    # 3. Ensemble calculation
    # Weights: 40% LSTM, 30% Prophet, 30% Scikit-learn
    w_lstm, w_prophet, w_sklearn = 0.40, 0.30, 0.30
    ensemble_next_day = (w_lstm * lstm_next_day) + (w_prophet * prophet_next_day) + (w_sklearn * sklearn_next_day)
    
    # Determine 7-day trend (using Prophet's long-term projection)
    percent_change_7d = ((prophet_7th_day - latest_close) / latest_close) * 100
    if percent_change_7d > 1.5:
        trend_7day = "BULLISH"
    elif percent_change_7d < -1.5:
        trend_7day = "BEARISH"
    else:
        trend_7day = "NEUTRAL"
        
    logger.info("--- Inference Results ---")
    logger.info(f"Prophet prediction:  ${prophet_next_day:,.2f}")
    logger.info(f"LSTM prediction:     ${lstm_next_day:,.2f}")
    logger.info(f"Sklearn prediction:  ${sklearn_next_day:,.2f}")
    logger.info(f"Ensemble prediction: ${ensemble_next_day:,.2f}")
    logger.info(f"7-Day Trend:         {trend_7day} ({percent_change_7d:+.2f}%)")
    logger.info("-------------------------")
    
    # 4. Construct prediction payloads for each model and insert into Supabase
    predictions_to_save = [
        {
            "model_used": "prophet",
            "prediction_type": "price_forecast",
            "predicted_value": prophet_next_day,
            "prediction_date": prediction_target_date,
            "confidence_score": 0.80
        },
        {
            "model_used": "lstm",
            "prediction_type": "price_forecast",
            "predicted_value": lstm_next_day,
            "prediction_date": prediction_target_date,
            "confidence_score": 0.85
        },
        {
            "model_used": "random_forest",
            "prediction_type": "price_forecast",
            "predicted_value": sklearn_next_day,
            "prediction_date": prediction_target_date,
            "confidence_score": 0.75
        },
        {
            "model_used": "ensemble",
            "prediction_type": "price_forecast",
            "predicted_value": ensemble_next_day,
            "prediction_date": prediction_target_date,
            "confidence_score": 0.90
        }
    ]
    
    saved_records = []
    for pred in predictions_to_save:
        res = insert_prediction(pred)
        if res.get("status") == "success":
            saved_records.append(res.get("data"))
            
    logger.info(f"Saved {len(saved_records)} prediction records to Supabase.")
    
    # Return composite representation of prediction results
    return {
        "prediction_date": prediction_target_date,
        "latest_close": latest_close,
        "prophet_price": prophet_next_day,
        "lstm_price": lstm_next_day,
        "sklearn_price": sklearn_next_day,
        "ensemble_price": ensemble_next_day,
        "trend_7day": trend_7day,
        "percent_change_7d": percent_change_7d,
        "saved_count": len(saved_records)
    }

if __name__ == "__main__":
    generate_predictions()
