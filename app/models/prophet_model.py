import os
import pickle
import numpy as np
import pandas as pd
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error
from app.core.logger import get_logger

logger = get_logger("prophet_model")

# Default path where trained model artifacts are saved
MODEL_DIR = "data/saved_models"
MODEL_PATH = os.path.join(MODEL_DIR, "prophet_model.pkl")
os.makedirs(MODEL_DIR, exist_ok=True)


def _prepare_prophet_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert a standard historical DataFrame (with 'date' + 'close' columns)
    into the Prophet-required format with 'ds' and 'y' columns.
    """
    prophet_df = df[["date", "close"]].copy()
    prophet_df.columns = ["ds", "y"]
    prophet_df["ds"] = pd.to_datetime(prophet_df["ds"])
    prophet_df = prophet_df.sort_values("ds").reset_index(drop=True)
    return prophet_df


def train(df: pd.DataFrame) -> Prophet:
    """
    Train a Facebook Prophet model on historical Bitcoin close prices.

    Args:
        df: DataFrame with at least 'date' and 'close' columns.

    Returns:
        Fitted Prophet model instance.
    """
    logger.info("Training Prophet model...")
    prophet_df = _prepare_prophet_df(df)

    # Bitcoin trades 24/7 and exhibits strong weekly + yearly seasonality
    model = Prophet(
        daily_seasonality=True,
        weekly_seasonality=True,
        yearly_seasonality=True,
        changepoint_prior_scale=0.05,    # Controls trend flexibility
        seasonality_prior_scale=10.0     # Controls seasonality flexibility
    )
    model.fit(prophet_df)
    logger.info(f"Prophet model trained on {len(prophet_df)} data points.")
    return model


def predict_next_7_days(model: Prophet) -> pd.DataFrame:
    """
    Generate predictions for the next 7 days using the trained Prophet model.

    Args:
        model: Fitted Prophet model instance.

    Returns:
        DataFrame with columns: ds (date), yhat, yhat_lower, yhat_upper.
    """
    # Create future dataframe for the next 7 days only (exclude history)
    future = model.make_future_dataframe(periods=7, freq="D", include_history=False)
    forecast = model.predict(future)

    result = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
    result = result.rename(columns={"ds": "date"})
    result["date"] = result["date"].dt.date
    logger.info(f"Prophet 7-day forecast generated for dates: {result['date'].tolist()}")
    return result


def evaluate(model: Prophet, df: pd.DataFrame) -> dict:
    """
    Evaluate Prophet model performance using in-sample predictions.

    Args:
        model: Fitted Prophet model instance.
        df:    DataFrame with at least 'date' and 'close' columns.

    Returns:
        Dict with MAE, RMSE, MAPE (as percentage string).
    """
    prophet_df = _prepare_prophet_df(df)
    forecast = model.predict(prophet_df)

    y_true = prophet_df["y"].values
    y_pred = forecast["yhat"].values

    mae  = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mape = float(np.mean(np.abs((y_true - y_pred) / (y_true + 1e-10))) * 100)

    metrics = {"mae": round(mae, 2), "rmse": round(rmse, 2), "mape": round(mape, 4)}
    logger.info(f"Prophet evaluation — MAE: {mae:.2f}, RMSE: {rmse:.2f}, MAPE: {mape:.4f}%")
    return metrics


def save_model(model: Prophet, path: str = MODEL_PATH) -> None:
    """
    Serialize and save the trained Prophet model to disk using pickle.

    Args:
        model: Fitted Prophet model.
        path:  File path to save the pickle file.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(model, f)
    logger.info(f"Prophet model saved to {path}")


def load_model(path: str = MODEL_PATH) -> Prophet:
    """
    Load a serialized Prophet model from disk.

    Args:
        path: File path of the pickle file.

    Returns:
        Deserialized Prophet model instance.

    Raises:
        FileNotFoundError: If the model file does not exist.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Prophet model not found at path: {path}. Please run training first.")
    with open(path, "rb") as f:
        model = pickle.load(f)
    logger.info(f"Prophet model loaded from {path}")
    return model
