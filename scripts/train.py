import os
import sys
import pandas as pd
from datetime import datetime

# Adjust Python path to resolve app modules from root directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.supabase_service import get_historical_data
from app.services.data_service import fetch_from_yfinance, fetch_from_coingecko, merge_and_clean, add_technical_indicators
from app.models.prophet_model import ProphetModelWrapper
from app.models.lstm_model import LSTMModelWrapper
from app.models.regressor_model import RegressorModelWrapper
from app.core.logger import get_logger
from datetime import datetime, timedelta

logger = get_logger("train_pipeline")

def load_training_data() -> pd.DataFrame:
    """
    Load training data from Supabase database. If empty, fall back to fetching from API.
    """
    logger.info("Loading training data from Supabase database...")
    try:
        # Load up to 3 years of data (approx 1095 days)
        df_db = get_historical_data(days=1095)
        if not df_db.empty and len(df_db) > 100:
            logger.info(f"Loaded {len(df_db)} records from Supabase database for training.")
            df_indicators = add_technical_indicators(df_db)
            return df_indicators
    except Exception as e:
        logger.error(f"Failed to load data from database: {e}. Falling back to API...")

    # Fallback to fetching directly from API
    logger.info("Database empty or insufficient. Fetching training data directly from APIs...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3 * 365)
    
    try:
        raw_df = fetch_from_yfinance(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    except Exception as yf_err:
        logger.warning(f"yfinance fetch failed: {yf_err}. Using CoinGecko fallback...")
        raw_df = fetch_from_coingecko(days=1095)
        
    df_cleaned = merge_and_clean(raw_df)
    df_indicators = add_technical_indicators(df_cleaned)
    return df_indicators

def main():
    logger.info("=" * 60)
    logger.info("STARTING BITCOIN PREDICTION MODEL TRAINING PIPELINE")
    logger.info("=" * 60)
    
    try:
        # Load historical data
        df = load_training_data()
        
        # 1. Train Prophet Model
        prophet_wrapper = ProphetModelWrapper()
        prophet_metrics = prophet_wrapper.train(df)
        logger.info(f"Prophet Training complete. In-Sample MAPE: {prophet_metrics['mape']:.2f}%")
        
        # 2. Train LSTM Model
        lstm_wrapper = LSTMModelWrapper(lookback=30)
        lstm_metrics = lstm_wrapper.train(df, epochs=20, batch_size=32)
        logger.info(f"LSTM Training complete. Training Loss: {lstm_metrics['loss']:.6f}")
        
        # 3. Train Scikit-learn Regressor
        sklearn_wrapper = RegressorModelWrapper()
        sklearn_metrics = sklearn_wrapper.train(df)
        logger.info(f"Scikit-learn Regressor complete. Test MAPE: {sklearn_metrics['mape']:.2f}%")
        
        logger.info("=" * 60)
        logger.info("ALL MODELS TRAINED AND SAVED SUCCESSFULLY")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Training pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
