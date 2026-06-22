import os
import pickle
import numpy as np
import pandas as pd
from prophet import Prophet
from app.core.logger import get_logger

logger = get_logger("prophet_model")

class ProphetModelWrapper:
    def __init__(self, model_dir: str = "data/saved_models"):
        self.model_dir = model_dir
        self.model_path = os.path.join(model_dir, "prophet_model.pkl")
        self.model = None
        os.makedirs(model_dir, exist_ok=True)

    def train(self, df: pd.DataFrame) -> dict:
        """
        Train Prophet model.
        df should contain 'date' and 'close' columns.
        """
        logger.info("Training Prophet Model...")
        # Prophet requires columns 'ds' and 'y'
        prophet_df = df[['date', 'close']].copy()
        prophet_df.columns = ['ds', 'y']
        
        # Ensure ds is datetime
        prophet_df['ds'] = pd.to_datetime(prophet_df['ds'])
        
        # Initialize Prophet with daily seasonality (as BTC trades 24/7)
        self.model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=True,
            changepoint_prior_scale=0.05
        )
        
        self.model.fit(prophet_df)
        
        # Save model
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
        
        logger.info(f"Prophet Model saved to {self.model_path}")
        
        # Return basic metrics (in-sample error)
        forecast = self.model.predict(prophet_df)
        y_true = prophet_df['y'].values
        y_pred = forecast['yhat'].values
        mape = float(np.mean(np.abs((y_true - y_pred) / y_true)) * 100)
        
        return {"mape": mape}

    def load(self) -> bool:
        """
        Load the trained model from disk.
        """
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                return True
            except Exception as e:
                logger.error(f"Error loading Prophet model: {e}")
        return False

    def predict_next_days(self, days: int = 7) -> list[float]:
        """
        Predict the close price for the next N days.
        Returns a list of predicted prices.
        """
        if not self.model:
            if not self.load():
                raise RuntimeError("Prophet model is not trained or loaded.")
        
        # Generate future dates dataframe
        future = self.model.make_future_dataframe(periods=days, freq='D', include_history=False)
        forecast = self.model.predict(future)
        
        # Extract yhat predictions
        predictions = forecast['yhat'].tolist()
        return predictions
