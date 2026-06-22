import os
# ─── FORCE CPU-ONLY: Must be set BEFORE importing TensorFlow ───────────────
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # Suppress TF INFO / WARNING logs

import pickle
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error

import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model as tf_load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping

from app.core.logger import get_logger

logger = get_logger("lstm_model")

# Default paths for saved model artifacts
MODEL_DIR   = "data/saved_models"
MODEL_PATH  = os.path.join(MODEL_DIR, "lstm_model.keras")
SCALER_PATH = os.path.join(MODEL_DIR, "lstm_scaler.pkl")
os.makedirs(MODEL_DIR, exist_ok=True)

SEQUENCE_LENGTH = 60  # Number of past days fed into each LSTM input window


def _build_sequences(scaled: np.ndarray, seq_len: int) -> tuple:
    """
    Construct sliding window input/output sequences for LSTM training.

    Args:
        scaled:  2D array of scaled close prices, shape (N, 1).
        seq_len: Lookback window length.

    Returns:
        Tuple (X, y) where X has shape (N-seq_len, seq_len, 1) and y has shape (N-seq_len,).
    """
    X, y = [], []
    for i in range(len(scaled) - seq_len):
        X.append(scaled[i : i + seq_len])
        y.append(scaled[i + seq_len])
    return np.array(X), np.array(y)


def train(df: pd.DataFrame, epochs: int = 50, batch_size: int = 32) -> tuple:
    """
    Train a 2-layer LSTM model on Bitcoin close prices (CPU only).

    Architecture:
        LSTM(100 units, return_sequences=True) → Dropout(0.2)
        LSTM(50 units)                          → Dropout(0.2)
        Dense(25)                               → Dense(1)

    Args:
        df:         DataFrame with at least 'date' and 'close' columns.
        epochs:     Training epochs (default 50, early stopping applies).
        batch_size: Mini-batch size (default 32).

    Returns:
        Tuple (model, scaler) — trained Keras model and fitted MinMaxScaler.
    """
    logger.info(f"Training LSTM model (CPU) — Sequence length: {SEQUENCE_LENGTH}, epochs: {epochs}...")

    df_sorted   = df.sort_values("date").reset_index(drop=True)
    close_prices = df_sorted["close"].values.reshape(-1, 1)

    if len(close_prices) < SEQUENCE_LENGTH + 30:
        raise ValueError(f"Dataset too small for LSTM: {len(close_prices)} rows (need > {SEQUENCE_LENGTH + 30}).")

    # Scale prices to [0, 1] using MinMaxScaler
    scaler        = MinMaxScaler(feature_range=(0, 1))
    scaled_prices = scaler.fit_transform(close_prices)

    # Build sliding window sequences
    X, y = _build_sequences(scaled_prices, SEQUENCE_LENGTH)
    # Reshape X for Keras: (samples, time_steps, features=1)
    X = X.reshape((X.shape[0], X.shape[1], 1))

    # Time-series train/validation split (no shuffling to avoid data leakage)
    split_idx = int(len(X) * 0.9)
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]

    # Build 2-layer LSTM model
    model = Sequential([
        LSTM(units=100, return_sequences=True, input_shape=(SEQUENCE_LENGTH, 1)),
        Dropout(0.2),
        LSTM(units=50, return_sequences=False),
        Dropout(0.2),
        Dense(units=25, activation="relu"),
        Dense(units=1)
    ])

    model.compile(optimizer="adam", loss="mean_squared_error")

    # Early stopping to prevent overfitting
    early_stop = EarlyStopping(
        monitor="val_loss",
        patience=8,
        restore_best_weights=True,
        verbose=0
    )

    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=[early_stop],
        verbose=0
    )

    # Persist model and scaler
    save_model(model, scaler)

    final_train_loss = history.history["loss"][-1]
    final_val_loss   = history.history.get("val_loss", [0])[-1]
    actual_epochs    = len(history.history["loss"])

    logger.info(f"LSTM Training complete — Epochs: {actual_epochs}, "
                f"Train Loss: {final_train_loss:.6f}, Val Loss: {final_val_loss:.6f}")
    return model, scaler


def predict_next_day(model, scaler: MinMaxScaler, df: pd.DataFrame) -> float:
    """
    Predict the next trading day's Bitcoin close price.

    Args:
        model:  Trained Keras LSTM model.
        scaler: Fitted MinMaxScaler (must be the one from training).
        df:     DataFrame with at least 'close' column, sorted by date.

    Returns:
        Predicted close price as a float.
    """
    df_sorted = df.sort_values("date").reset_index(drop=True)

    if len(df_sorted) < SEQUENCE_LENGTH:
        raise ValueError(f"Need at least {SEQUENCE_LENGTH} data points for LSTM prediction, got {len(df_sorted)}.")

    # Extract and scale the most recent 60 closing prices
    recent_prices = df_sorted["close"].values[-SEQUENCE_LENGTH:].reshape(-1, 1)
    scaled_input  = scaler.transform(recent_prices)

    # Reshape to (1, SEQUENCE_LENGTH, 1) for model inference
    X_input     = scaled_input.reshape((1, SEQUENCE_LENGTH, 1))
    scaled_pred = model.predict(X_input, verbose=0)

    # Inverse transform to get the actual price
    pred_price = scaler.inverse_transform(scaled_pred)
    result = float(pred_price[0, 0])
    logger.info(f"LSTM next-day price prediction: ${result:,.2f}")
    return result


def evaluate(model, scaler: MinMaxScaler, df: pd.DataFrame) -> dict:
    """
    Evaluate the LSTM model on held-out test data.

    Args:
        model:  Trained Keras LSTM model.
        scaler: Fitted MinMaxScaler.
        df:     Full historical DataFrame.

    Returns:
        Dict with MAE and RMSE (in USD).
    """
    df_sorted    = df.sort_values("date").reset_index(drop=True)
    close_prices = df_sorted["close"].values.reshape(-1, 1)
    scaled       = scaler.transform(close_prices)

    X, y = _build_sequences(scaled, SEQUENCE_LENGTH)
    X    = X.reshape((X.shape[0], X.shape[1], 1))

    # Use last 10% for evaluation
    split = int(len(X) * 0.9)
    X_test, y_test_scaled = X[split:], y[split:]

    if len(X_test) == 0:
        logger.warning("Not enough data for LSTM evaluation test set.")
        return {"mae": None, "rmse": None}

    y_pred_scaled = model.predict(X_test, verbose=0)

    # Inverse transform to price space
    y_true = scaler.inverse_transform(y_test_scaled.reshape(-1, 1)).flatten()
    y_pred = scaler.inverse_transform(y_pred_scaled).flatten()

    mae  = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))

    metrics = {"mae": round(mae, 2), "rmse": round(rmse, 2)}
    logger.info(f"LSTM Evaluation — MAE: ${mae:.2f}, RMSE: ${rmse:.2f}")
    return metrics


def save_model(model, scaler: MinMaxScaler, model_path: str = MODEL_PATH, scaler_path: str = SCALER_PATH) -> None:
    """
    Save both the Keras LSTM model (.keras) and the MinMaxScaler (.pkl) to disk.

    Args:
        model:       Trained Keras model.
        scaler:      Fitted MinMaxScaler.
        model_path:  Destination path for the model file.
        scaler_path: Destination path for the scaler pickle.
    """
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    model.save(model_path)
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)
    logger.info(f"LSTM model saved to {model_path}")
    logger.info(f"LSTM scaler saved to {scaler_path}")


def load_model(model_path: str = MODEL_PATH, scaler_path: str = SCALER_PATH) -> tuple:
    """
    Load both the Keras LSTM model and the MinMaxScaler from disk.

    Args:
        model_path:  Path to the .keras model file.
        scaler_path: Path to the scaler pickle file.

    Returns:
        Tuple (model, scaler) — loaded Keras model and MinMaxScaler.

    Raises:
        FileNotFoundError: If either file is missing.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"LSTM model not found at {model_path}. Please train first.")
    if not os.path.exists(scaler_path):
        raise FileNotFoundError(f"LSTM scaler not found at {scaler_path}. Please train first.")

    model = tf_load_model(model_path)
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)
    logger.info(f"LSTM model loaded from {model_path}")
    return model, scaler
