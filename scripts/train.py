import os
import sys
import pandas as pd
from datetime import datetime

# Adjust Python path to resolve app modules from root directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, engine
from app.models.db_models import HistoricalPrice
from app.services.data_service import fetch_btc_data, add_technical_indicators
from app.models.prophet_model import ProphetModelWrapper
from app.models.lstm_model import LSTMModelWrapper
from app.models.regressor_model import RegressorModelWrapper
from app.core.logger import get_logger

logger = get_logger("train_pipeline")

def load_training_data() -> pd.DataFrame:
    """
    Load training data from Supabase database. If empty, fall back to fetching from yfinance.
    """
    if engine:
        try:
            db = SessionLocal()
            query = db.query(HistoricalPrice).order_by(HistoricalPrice.date.asc())
            df_db = pd.read_sql(query.statement, db.bind)
            db.close()
            
            if not df_db.empty and len(df_db) > 100:
                logger.info(f"Loaded {len(df_db)} records from Supabase database for training.")
                # Map db columns to expected data loader columns
                df_db = df_db.rename(columns={
                    "close_price": "close",
                    "open_price": "open",
                    "high_price": "high",
                    "low_price": "low"
                })
                return df_db
        except Exception as e:
            logger.error(f"Failed to load data from database: {e}. Falling back to yfinance...")

    # Fallback to yfinance directly
    logger.info("Fetching training data directly from yfinance...")
    raw_df = fetch_btc_data(period="2y")
    df_indicators = add_technical_indicators(raw_df)
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
