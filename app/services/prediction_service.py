import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from app.core.database import SessionLocal, engine
from app.models.db_models import Prediction, HistoricalPrice
from app.services.data_service import fetch_btc_data, add_technical_indicators, prepare_ml_features
from app.models.prophet_model import ProphetModelWrapper
from app.models.lstm_model import LSTMModelWrapper
from app.models.regressor_model import RegressorModelWrapper
from sqlalchemy.dialects.postgresql import insert
from app.core.logger import get_logger

logger = get_logger("prediction_service")

def generate_predictions() -> dict:
    """
    Generate predictions for the next trading day and 7-day trend.
    """
    # 1. Fetch latest data from yfinance (retrieve 60 days to have enough window for indicators + lookback)
    logger.info("Fetching latest data for inference...")
    raw_df = fetch_btc_data(period="60d")
    df = add_technical_indicators(raw_df)
    
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
    prophet_next_day = prophet_forecast[0] # Next day
    prophet_7th_day = prophet_forecast[6] # 7th day
    
    # LSTM Prediction
    lstm_wrapper = LSTMModelWrapper(lookback=30)
    # Get recent prices for LSTM input (at least 30 values)
    recent_prices = df.sort_values('date')['close'].values
    lstm_next_day = lstm_wrapper.predict_next_day(recent_prices)
    
    # Scikit-learn Regressor Prediction
    sklearn_wrapper = RegressorModelWrapper()
    # Prepare lag features (internally loads from disk)
    sklearn_next_day = sklearn_wrapper.predict_next_day(df)
    
    # 3. Ensemble calculation
    # Weights: 40% LSTM, 30% Prophet, 30% Scikit-learn
    w_lstm, w_prophet, w_sklearn = 0.40, 0.30, 0.30
    ensemble_next_day = (w_lstm * lstm_next_day) + (w_prophet * prophet_next_day) + (w_sklearn * sklearn_next_day)
    
    # 4. Determine direction (UP or DOWN) relative to latest close
    predicted_direction = "UP" if ensemble_next_day > latest_close else "DOWN"
    
    # 5. Determine 7-day trend (using Prophet's long-term projection)
    percent_change_7d = ((prophet_7th_day - latest_close) / latest_close) * 100
    if percent_change_7d > 1.5:
        trend_7day = "BULLISH"
    elif percent_change_7d < -1.5:
        trend_7day = "BEARISH"
    else:
        trend_7day = "NEUTRAL"
        
    prediction_result = {
        "prediction_date": prediction_target_date,
        "prophet_price": float(prophet_next_day),
        "lstm_price": float(lstm_next_day),
        "sklearn_price": float(sklearn_next_day),
        "ensemble_price": float(ensemble_next_day),
        "predicted_direction": predicted_direction,
        "trend_7day": trend_7day
    }
    
    logger.info("--- Inference Results ---")
    logger.info(f"Prophet prediction:  ${prophet_next_day:,.2f}")
    logger.info(f"LSTM prediction:     ${lstm_next_day:,.2f}")
    logger.info(f"Sklearn prediction:  ${sklearn_next_day:,.2f}")
    logger.info(f"Ensemble prediction: ${ensemble_next_day:,.2f}")
    logger.info(f"Predicted Direction: {predicted_direction}")
    logger.info(f"7-Day Trend:         {trend_7day} ({percent_change_7d:+.2f}%)")
    logger.info("-------------------------")
    
    # 6. Save prediction to Supabase
    if engine:
        try:
            db = SessionLocal()
            stmt = insert(Prediction).values(prediction_result)
            stmt = stmt.on_conflict_do_update(
                index_elements=["prediction_date"],
                set_={
                    "prophet_price": stmt.excluded.prophet_price,
                    "lstm_price": stmt.excluded.lstm_price,
                    "sklearn_price": stmt.excluded.sklearn_price,
                    "ensemble_price": stmt.excluded.ensemble_price,
                    "predicted_direction": stmt.excluded.predicted_direction,
                    "trend_7day": stmt.excluded.trend_7day,
                    "run_date": datetime.utcnow()
                }
            )
            db.execute(stmt)
            db.commit()
            db.close()
            logger.info("Successfully saved prediction to Supabase database.")
        except Exception as e:
            logger.error(f"Failed to save prediction to database: {e}")
            
    return prediction_result

if __name__ == "__main__":
    generate_predictions()
