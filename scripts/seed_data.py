import os
import sys
from datetime import datetime, timedelta

# Adjust Python path to resolve backend modules from root directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.data_service import fetch_from_yfinance, fetch_from_coingecko, merge_and_clean, add_technical_indicators
from app.services.supabase_service import insert_historical_data, supabase
from app.core.logger import get_logger

logger = get_logger("seed_data")

def main():
    logger.info("=" * 60)
    logger.info("STARTING BITCOIN 3-YEAR SEED DATA PIPELINE")
    logger.info("=" * 60)

    if not supabase:
        logger.error("❌ Supabase client is not initialized. Please set SUPABASE_URL and SUPABASE_KEY in .env.")
        sys.exit(1)

    # 1. Define date range for 3 years
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3 * 365)
    
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    logger.info(f"Target date range: {start_str} to {end_str}")

    # 2. Fetch data
    df_raw = None
    try:
        df_raw = fetch_from_yfinance(start_str, end_str)
        logger.info(f"Successfully fetched {len(df_raw)} records from yfinance.")
    except Exception as e:
        logger.warning(f"⚠️ Failed to fetch from yfinance: {e}. Trying CoinGecko fallback...")
        try:
            # CoinGecko market_chart days parameter supports up to 1095 days (~3 years)
            df_raw = fetch_from_coingecko(days=1095)
            logger.info(f"Successfully fetched {len(df_raw)} records from CoinGecko.")
        except Exception as cg_err:
            logger.error(f"❌ Critical: Fallback to CoinGecko also failed: {cg_err}")
            sys.exit(1)

    # 3. Clean and deduplicate data
    logger.info("Cleaning and formatting dataset...")
    df_cleaned = merge_and_clean(df_raw)
    logger.info(f"Dataset clean. Total records remaining: {len(df_cleaned)}")

    # 4. Enrich with indicators to test the indicator engine
    logger.info("Calculating technical indicators (SMAs, EMAs, RSI, MACD, Bollinger Bands, Volatility)...")
    df_enriched = add_technical_indicators(df_cleaned)
    logger.info(f"Technical indicators generated. Total enriched rows: {len(df_enriched)}")

    # 5. Insert cleaned data into Supabase btc_historical_data
    logger.info("Starting database insertion...")
    # insert_historical_data will extract only the schema columns (date, open, high, low, close, volume, source)
    res = insert_historical_data(df_cleaned)

    if res.get("status") == "success":
        print("\n" + "=" * 50)
        print("          SEED INGESTION COMPLETE")
        print("=" * 50)
        print(f" Rows Processed   : {len(df_cleaned)}")
        print(f" Rows Inserted    : {len(res.get('data', []))}")
        print(f" Data Source      : {df_cleaned['source'].iloc[0] if not df_cleaned.empty else 'Unknown'}")
        print(f" Indicators Run   : SUCCESS")
        print("=" * 50)
        logger.info("Seed data ingestion complete: SUCCESS.")
    else:
        logger.error(f"❌ Database insertion failed: {res.get('message')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
