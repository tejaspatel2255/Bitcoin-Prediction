import os
# Force CPU-only mode for TensorFlow
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import numpy as np
import pandas as pd
import pickle
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from app.core.logger import get_logger

logger = get_logger("lstm_model")

class LSTMModelWrapper:
    def __init__(self, model_dir: str = "data/saved_models", lookback: int = 30):
        self.model_dir = model_dir
        self.model_path = os.path.join(model_dir, "lstm_model.keras")
        self.scaler_path = os.path.join(model_dir, "lstm_scaler.pkl")
        self.lookback = lookback
        self.model = None
        self.scaler = None
        os.makedirs(model_dir, exist_ok=True)

    def prepare_data(self, prices: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """
        Create sliding window sequences for LSTM training.
        """
        X, y = [], []
        for i in range(len(prices) - self.lookback):
            X.append(prices[i : i + self.lookback])
            y.append(prices[i + self.lookback])
        return np.array(X), np.array(y)

    def train(self, df: pd.DataFrame, epochs: int = 20, batch_size: int = 32) -> dict:
        """
        Train the LSTM model using historical close prices.
        """
        logger.info("Training LSTM Model (CPU)...")
        # Ensure we are sorted by date
        df_sorted = df.sort_values('date').reset_index(drop=True)
        close_prices = df_sorted['close'].values.reshape(-1, 1)

        # Scale prices
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_prices = self.scaler.fit_transform(close_prices)

        # Create sequences
        X, y = self.prepare_data(scaled_prices)
        if len(X) == 0:
            raise ValueError("Dataset is too small for the specified lookback window.")

        # Reshape for LSTM input: (samples, time steps, features)
        X = X.reshape((X.shape[0], X.shape[1], 1))

        # Build model
        self.model = Sequential([
            LSTM(units=50, return_sequences=True, input_shape=(self.lookback, 1)),
            Dropout(0.2),
            LSTM(units=50, return_sequences=False),
            Dropout(0.2),
            Dense(units=25),
            Dense(units=1)
        ])

        self.model.compile(optimizer='adam', loss='mean_squared_error')
        
        # Train
        history = self.model.fit(
            X, y, 
            epochs=epochs, 
            batch_size=batch_size, 
            verbose=0,
            validation_split=0.1
        )

        # Save model and scaler
        self.model.save(self.model_path)
        with open(self.scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)

        logger.info(f"LSTM Model saved to {self.model_path}")
        logger.info(f"LSTM Scaler saved to {self.scaler_path}")

        # Compute training loss as performance metric
        final_loss = history.history['loss'][-1]
        return {"loss": float(final_loss)}

    def load(self) -> bool:
        """
        Load the trained model and scaler from disk.
        """
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            try:
                self.model = load_model(self.model_path)
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                return True
            except Exception as e:
                logger.error(f"Error loading LSTM model/scaler: {e}")
        return False

    def predict_next_day(self, historical_prices: np.ndarray) -> float:
        """
        Predict the next day's price given the most recent series of prices.
        historical_prices: Array of shape (lookback,) or larger.
        """
        if not self.model or not self.scaler:
            if not self.load():
                raise RuntimeError("LSTM model or scaler is not trained/loaded.")
        
        # Extract the last 'lookback' prices
        recent_prices = historical_prices[-self.lookback:].reshape(-1, 1)
        
        # Scale input
        scaled_input = self.scaler.transform(recent_prices)
        
        # Reshape for inference (1, lookback, 1)
        scaled_input = scaled_input.reshape((1, self.lookback, 1))
        
        # Predict and inverse scale
        scaled_pred = self.model.predict(scaled_input, verbose=0)
        pred_price = self.scaler.inverse_transform(scaled_pred)
        
        return float(pred_price[0, 0])
