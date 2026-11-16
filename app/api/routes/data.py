from fastapi import APIRouter, HTTPException, Query, status
from typing import List
import pandas as pd
from datetime import datetime, timedelta

from app.schemas.schemas import HistoricalDataResponse, RefreshDataResponse
from app.services.supabase_service import get_historical_data, insert_historical_data
from app.services.data_service import (
    fetch_from_yfinance, fetch_from_coingecko,
    merge_and_clean, add_technical_indicators
)
from app.core.logger import get_logger

logger = get_logger("api.routes.data")

router = APIRouter(
    prefix="/data",
    tags=["data"]
)

@router.get("/historical", response_model=List[HistoricalDataResponse])
def get_historical(days: int = Query(default=30, description="Number of historical days to fetch from Supabase", ge=1)):
    """
    Fetch historical Bitcoin price data from Supabase, calculate technical indicators,
    and return the enriched dataset.
    """
    logger.info(f"API: Fetching last {days} days of historical BTC data from Supabase")
    try:
        # Fetch days + 60 days of historical data to ensure indicators (e.g. 50 SMA) have enough warm-up history
        warm_up_days = days + 60
        df = get_historical_data(days=warm_up_days)
        
        if df.empty:
            logger.warning("No historical data found in Supabase.")
            return []
            
        # Enrich dataset with technical indicators
        df_indicators = add_technical_indicators(df)
        
        # Sort and limit to the requested number of days
        df_sorted = df_indicators.sort_values("date", ascending=True)
        df_filtered = df_sorted.tail(days)
        
        records = df_filtered.to_dict(orient="records")
        return records
    except Exception as e:
        logger.error(f"Error in GET /api/data/historical: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch historical data: {str(e)}"
        )

@router.post("/refresh", response_model=RefreshDataResponse)
def refresh_data():
    """
    Trigger a fresh data fetch for the last 30 days from live APIs (yfinance with CoinGecko fallback)
    and store the results into the Supabase database.
    """
    logger.info("API: Triggering manual data refresh/ingestion")
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Try fetching from yfinance first
        try:
            df = fetch_from_yfinance(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        except Exception as yf_err:
            logger.warning(f"yfinance fetch failed: {yf_err}. Attempting CoinGecko fallback...")
            df = fetch_from_coingecko(days=30)
            
        df_cleaned = merge_and_clean(df)
        if df_cleaned.empty:
            return RefreshDataResponse(
                status="success",
                message="Data fetch completed, but no new data points were found.",
                rows_added=0
            )
            
        # Insert/upsert into Supabase btc_historical_data table
        res = insert_historical_data(df_cleaned)
        
        if res.get("status") == "success":
            count = res.get("count", 0)
            logger.info(f"Manual data refresh successful. Ingested {count} rows.")
            return RefreshDataResponse(
                status="success",
                message=f"Successfully ingested and updated Bitcoin market data.",
                rows_added=count
            )
        else:
            raise Exception(res.get("message", "Unknown database insert error"))
            
    except Exception as e:
        logger.error(f"Error in POST /api/data/refresh: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh data: {str(e)}"
        )
