import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime, timedelta
from app.core.logger import get_logger

logger = get_logger("data_service")

def fetch_btc_data(period: str = "2y", interval: str = "1d") -> pd.DataFrame:
    """
    Fetch historical Bitcoin price data from yfinance.
    """
    logger.info(f"Fetching BTC-USD historical data for period={period}, interval={interval}...")
    ticker = yf.Ticker("BTC-USD")
    df = ticker.history(period=period, interval=interval)
    
    if df.empty:
        raise ValueError("No data returned from yfinance for BTC-USD.")
    
    # Reset index to make Date a column
    df = df.reset_index()
    # Normalize column names to lowercase and remove spaces
    df.columns = [col.lower().replace(" ", "_") for col in df.columns]
    
    # Ensure date column is datetime.date type
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date']).dt.date
    
    return df

def calculate_rsi(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """
    Calculate the Relative Strength Index (RSI).
    """
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).copy()
    loss = (-delta.where(delta < 0, 0)).copy()
    
    # Calculate EMA of gain and loss
    avg_gain = gain.ewm(com=window - 1, min_periods=window).mean()
    avg_loss = loss.ewm(com=window - 1, min_periods=window).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(df: pd.DataFrame, span_fast: int = 12, span_slow: int = 26, signal: int = 9) -> tuple[pd.Series, pd.Series]:
    """
    Calculate the Moving Average Convergence Divergence (MACD) and its signal line.
    """
    ema_fast = df['close'].ewm(span=span_fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=span_slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line

def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate and append technical indicators to the DataFrame.
    """
    df = df.copy()
    
    # Sort by date to ensure correct rolling calculations
    df = df.sort_values('date').reset_index(drop=True)
    
    # Calculate indicators
    df['rsi_14'] = calculate_rsi(df, window=14)
    df['macd'], df['macd_signal'] = calculate_macd(df)
    
    # Add simple moving averages for feature engineering
    df['sma_7'] = df['close'].rolling(window=7).mean()
    df['sma_30'] = df['close'].rolling(window=30).mean()
    
    # Replace NaN values resulting from rolling window with 0 or forward fill
    df = df.fillna(0)
    
    return df

def prepare_ml_features(df: pd.DataFrame, target_lead: int = 1) -> pd.DataFrame:
    """
    Prepare feature dataset for supervised learning models (like scikit-learn Regressors).
    """
    df = df.copy()
    df = df.sort_values('date').reset_index(drop=True)
    
    # Create lag features (e.g. historical values of close price, volume, indicators)
    for lag in [1, 2, 3, 5, 7]:
        df[f'close_lag_{lag}'] = df['close'].shift(lag)
        df[f'vol_lag_{lag}'] = df['volume'].shift(lag)
        df[f'rsi_lag_{lag}'] = df['rsi_14'].shift(lag)
        
    # Target value is the close price of 'target_lead' days in the future
    df['target_price'] = df['close'].shift(-target_lead)
    
    # Binary direction target (1 if next close > current close, else 0)
    df['target_direction'] = (df['target_price'] > df['close']).astype(int)
    
    # Drop rows with NaN (from shifts)
    df = df.dropna().reset_index(drop=True)
    
    return df

def fetch_coingecko_price() -> float:
    """
    Fetch the current real-time close price of Bitcoin from CoinGecko API.
    """
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()
        price = float(data["bitcoin"]["usd"])
        logger.info(f"Fetched live price from CoinGecko: ${price:,.2f}")
        return price
    except Exception as e:
        logger.error(f"Error fetching live price from CoinGecko: {e}")
        # Fallback to fetching live price from yfinance
        try:
            logger.info("Attempting fallback price fetch using yfinance...")
            ticker = yf.Ticker("BTC-USD")
            df = ticker.history(period="1d")
            if not df.empty:
                price = float(df['Close'].iloc[-1])
                logger.info(f"Fallback: Fetched live price from yfinance: ${price:,.2f}")
                return price
        except Exception as yf_err:
            logger.error(f"Fallback to yfinance also failed: {yf_err}")
        raise e
