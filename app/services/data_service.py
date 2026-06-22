import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.logger import get_logger
from app.core.config import settings

logger = get_logger("data_service")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.RequestException, Exception)),
    reraise=True
)
def fetch_from_yfinance(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch historical Bitcoin price data from yfinance.
    Columns returned: date (datetime.date), open, high, low, close, volume, source
    """
    logger.info(f"Fetching BTC-USD from yfinance from {start_date} to {end_date}...")
    ticker = yf.Ticker("BTC-USD")
    df = ticker.history(start=start_date, end=end_date, interval="1d")
    
    if df.empty:
        raise ValueError(f"No data returned from yfinance for BTC-USD in range {start_date} to {end_date}.")
        
    df = df.reset_index()
    # Map to standard lowercase names
    df.columns = [col.lower().replace(" ", "_") for col in df.columns]
    
    # Select and rename to schema columns
    df = df.rename(columns={"date": "date", "open": "open", "high": "high", "low": "low", "close": "close", "volume": "volume"})
    df['date'] = pd.to_datetime(df['date']).dt.date
    df['source'] = 'yfinance'
    
    return df[['date', 'open', 'high', 'low', 'close', 'volume', 'source']]

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.RequestException, Exception)),
    reraise=True
)
def fetch_from_coingecko(days: int = 365) -> pd.DataFrame:
    """
    Fetch historical Bitcoin price data from CoinGecko API.
    Columns returned: date (datetime.date), open, high, low, close, volume, source
    """
    logger.info(f"Fetching BTC-USD from CoinGecko for the last {days} days...")
    url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days={days}&interval=daily"
    res = requests.get(url, timeout=10)
    res.raise_for_status()
    data = res.json()
    
    prices = data.get("prices", [])
    volumes = data.get("total_volumes", [])
    
    if not prices:
        raise ValueError("No data returned from CoinGecko API.")
        
    records = []
    # CoinGecko daily returns a list of [timestamp_ms, value]
    # Keep in mind volumes might have slightly different count, so we align by index or key
    vol_dict = {int(v[0]): float(v[1]) for v in volumes}
    
    for item in prices:
        ts = int(item[0])
        close_price = float(item[1])
        dt = datetime.fromtimestamp(ts / 1000.0).date()
        vol = vol_dict.get(ts, 0.0)
        
        records.append({
            "date": dt,
            "open": close_price, # CG does not provide OHLC in market_chart, so we approximate
            "high": close_price,
            "low": close_price,
            "close": close_price,
            "volume": vol,
            "source": "coingecko"
        })
        
    df = pd.DataFrame(records)
    return df

def merge_and_clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge and clean the Bitcoin price DataFrame (deduplicate, handle nulls, and clean outliers).
    """
    if df.empty:
        return df
        
    df = df.copy()
    
    # Convert date to standard datetime.date format if not already
    df['date'] = pd.to_datetime(df['date']).dt.date
    
    # 1. Deduplicate by date (keep first occurrence)
    df = df.drop_duplicates(subset=['date'], keep='first')
    
    # 2. Sort by date ascending
    df = df.sort_values('date').reset_index(drop=True)
    
    # 3. Handle null values
    df = df.dropna(subset=['close'])
    df['open'] = df['open'].fillna(df['close'])
    df['high'] = df['high'].fillna(df['close'])
    df['low'] = df['low'].fillna(df['close'])
    df['volume'] = df['volume'].fillna(0.0)
    
    # 4. Outlier detection and cleaning
    # Remove rows where close price is negative or zero
    df = df[df['close'] > 0]
    
    # If high < close, set high = max(high, close)
    df['high'] = df[['high', 'close']].max(axis=1)
    # If low > close, set low = min(low, close)
    df['low'] = df[['low', 'close']].min(axis=1)
    
    return df.reset_index(drop=True)

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
    
    rs = avg_gain / (avg_loss + 1e-10)
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
    Calculate and append all technical indicators required for forecasting models.
    """
    if df.empty:
        return df
        
    df = df.copy()
    df = df.sort_values('date').reset_index(drop=True)
    
    # 1. SMAs (7, 21, 50 day)
    df['sma_7'] = df['close'].rolling(window=7, min_periods=1).mean()
    df['sma_21'] = df['close'].rolling(window=21, min_periods=1).mean()
    df['sma_50'] = df['close'].rolling(window=50, min_periods=1).mean()
    
    # 2. EMAs (12, 26 day)
    df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
    
    # 3. RSI (14 day)
    df['rsi_14'] = calculate_rsi(df, window=14)
    
    # 4. MACD + Signal line
    df['macd'], df['macd_signal'] = calculate_macd(df)
    
    # 5. Bollinger Bands (upper, lower, mid)
    df['bb_mid'] = df['close'].rolling(window=20, min_periods=1).mean()
    bb_std = df['close'].rolling(window=20, min_periods=1).std().fillna(0)
    df['bb_upper'] = df['bb_mid'] + 2 * bb_std
    df['bb_lower'] = df['bb_mid'] - 2 * bb_std
    
    # 6. Daily returns & log returns
    df['daily_return'] = df['close'].pct_change().fillna(0.0)
    df['log_return'] = np.log(df['close'] / df['close'].shift(1).fillna(df['close'])).fillna(0.0)
    
    # 7. Volume moving average (20-day SMA of Volume)
    df['volume_sma'] = df['volume'].rolling(window=20, min_periods=1).mean()
    
    # 8. Volatility (rolling std of returns)
    df['volatility'] = df['daily_return'].rolling(window=20, min_periods=1).std().fillna(0.0)
    
    # Replace any remaining NaNs with 0
    df = df.fillna(0.0)
    
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

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.RequestException, Exception)),
    reraise=True
)
def fetch_coingecko_price() -> float:
    """
    Fetch the current real-time close price of Bitcoin from CoinGecko API with retry.
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

def scheduled_ingestion_job():
    """
    Job run by APScheduler to fetch the last 30 days of data and upsert to Supabase.
    """
    logger.info("Starting scheduled BTC data ingestion job...")
    from app.services.supabase_service import insert_historical_data
    
    try:
        # Fetch the last 30 days to capture recent changes and ensure indicator rolling history is updated
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        try:
            df = fetch_from_yfinance(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        except Exception as yf_err:
            logger.warning(f"yfinance failed in scheduled job: {yf_err}. Attempting CoinGecko fallback...")
            df = fetch_from_coingecko(days=30)
            
        df_cleaned = merge_and_clean(df)
        
        # Save raw historical price data into Supabase btc_historical_data table
        res = insert_historical_data(df_cleaned)
        
        if res.get("status") == "success":
            logger.info(f"Scheduled ingestion successfully upserted {res.get('count', 0)} records.")
        else:
            logger.error(f"Scheduled ingestion database insert failed: {res.get('message')}")
            
    except Exception as e:
        logger.error(f"Scheduled ingestion job failed: {e}")

def start_data_scheduler():
    """
    Start the APScheduler background scheduler for data ingestion every 6 hours.
    """
    scheduler = BackgroundScheduler()
    # Run every 6 hours
    scheduler.add_job(scheduled_ingestion_job, 'interval', hours=6, id='btc_scheduled_ingest')
    scheduler.start()
    logger.info("APScheduler initialized and running background jobs (btc_scheduled_ingest: every 6 hours).")
    return scheduler

