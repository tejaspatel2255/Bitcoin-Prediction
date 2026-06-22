import os
import pickle
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_percentage_error
from app.services.data_service import prepare_ml_features
from app.core.logger import get_logger

logger = get_logger("regressor_model")

class RegressorModelWrapper:
    def __init__(self, model_dir: str = "data/saved_models"):
        self.model_dir = model_dir
        self.model_path = os.path.join(model_dir, "sklearn_model.pkl")
        self.features_path = os.path.join(model_dir, "sklearn_features.pkl")
        self.model = None
        self.feature_cols = []
        os.makedirs(model_dir, exist_ok=True)

    def train(self, df: pd.DataFrame) -> dict:
        """
        Train the scikit-learn Random Forest model on technical and lag features.
        """
        logger.info("Training Scikit-learn Regressor Model...")
        # Prepare supervised features
        ml_df = prepare_ml_features(df, target_lead=1)
        
        if len(ml_df) < 50:
            raise ValueError("Not enough historical data to generate lag features for training.")
        
        # Define features and target
        # Features are everything except dates, target values, and ID-like fields
        exclude_cols = ['date', 'target_price', 'target_direction']
        self.feature_cols = [col for col in ml_df.columns if col not in exclude_cols]
        
        X = ml_df[self.feature_cols].values
        y = ml_df['target_price'].values
        
        # Define train/test split (80/20 sequential split to preserve time series)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Fit Random Forest Regressor
        self.model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        self.model.fit(X_train, y_train)
        
        # Evaluate model
        y_pred = self.model.predict(X_test)
        mape = float(mean_absolute_percentage_error(y_test, y_pred) * 100)
        
        # Save model and feature list
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
        with open(self.features_path, 'wb') as f:
            pickle.dump(self.feature_cols, f)
            
        logger.info(f"Scikit-learn Model saved to {self.model_path}")
        logger.info(f"Scikit-learn Feature List saved to {self.features_path}")
        
        return {"mape": mape}

    def load(self) -> bool:
        """
        Load the trained model and feature list from disk.
        """
        if os.path.exists(self.model_path) and os.path.exists(self.features_path):
            try:
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                with open(self.features_path, 'rb') as f:
                    self.feature_cols = pickle.load(f)
                return True
            except Exception as e:
                logger.error(f"Error loading Scikit-learn model: {e}")
        return False

    def predict_next_day(self, df_latest: pd.DataFrame) -> float:
        """
        Predict the next day's price using the latest day's indicators/features.
        df_latest should contain the same feature columns that were used to train.
        """
        if not self.model or not self.feature_cols:
            if not self.load():
                raise RuntimeError("Scikit-learn model or feature list is not trained/loaded.")
        
        # Ensure we have the required columns
        missing_cols = [col for col in self.feature_cols if col not in df_latest.columns]
        if missing_cols:
            raise ValueError(f"Missing required feature columns for prediction: {missing_cols}")
            
        # Get the very latest row
        latest_row = df_latest.sort_values('date').iloc[-1:]
        X_latest = latest_row[self.feature_cols].values
        
        pred = self.model.predict(X_latest)
        return float(pred[0])
