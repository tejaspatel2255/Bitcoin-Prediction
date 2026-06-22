import os
import sys
import pandas as pd
from datetime import datetime

# Adjust Python path to resolve backend modules from root directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, engine
from app.models.db_models import HistoricalPrice
from app.services.data_service import fetch_btc_data, add_technical_indicators
from sqlalchemy.dialects.postgresql import insert

def ingest_historical_data(period: str = "2y"):
    """
    Fetch Bitcoin data, calculate indicators, and upsert into the Supabase database.
    """
    if not engine:
        print("Database not configured. Make sure SUPABASE_DB_URL is set in your .env file.")
        return

    try:
        # 1. Fetch raw data and add indicators
        raw_df = fetch_btc_data(period=period)
        df_indicators = add_technical_indicators(raw_df)
        
        print(f"Prepared {len(df_indicators)} rows of historical data with technical indicators.")
        
        # 2. Insert or update (upsert) in the database
        db = SessionLocal()
        count = 0
        
        for _, row in df_indicators.iterrows():
            # Prepare data dict mapping to the db columns
            data_dict = {
                "date": row["date"],
                "close_price": float(row["close"]),
                "open_price": float(row["open"]),
                "high_price": float(row["high"]),
                "low_price": float(row["low"]),
                "volume": float(row["volume"]),
                "rsi_14": float(row["rsi_14"]) if row["rsi_14"] != 0 else None,
                "macd": float(row["macd"]) if row["macd"] != 0 else None,
                "macd_signal": float(row["macd_signal"]) if row["macd_signal"] != 0 else None,
            }
            
            # Use PostgreSQL upsert (insert ... on conflict (date) do update)
            stmt = insert(HistoricalPrice).values(data_dict)
            stmt = stmt.on_conflict_do_update(
                index_elements=["date"],
                set_={
                    "close_price": stmt.excluded.close_price,
                    "open_price": stmt.excluded.open_price,
                    "high_price": stmt.excluded.high_price,
                    "low_price": stmt.excluded.low_price,
                    "volume": stmt.excluded.volume,
                    "rsi_14": stmt.excluded.rsi_14,
                    "macd": stmt.excluded.macd,
                    "macd_signal": stmt.excluded.macd_signal,
                }
            )
            
            db.execute(stmt)
            count += 1
            if count % 100 == 0:
                db.commit()
                print(f"Upserted {count} records...")
                
        db.commit()
        db.close()
        print(f"Successfully finished data ingestion! Total records processed: {count}")
        
    except Exception as e:
        print(f"Error during ingestion pipeline: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # If arguments are passed, allow custom period (e.g. 30d, 5y)
    period = "2y"
    if len(sys.argv) > 1:
        period = sys.argv[1]
    ingest_historical_data(period=period)
