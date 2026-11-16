from fastapi import APIRouter, Query, HTTPException
from app.services.supabase_service import get_historical_data
from app.services.data_service import add_technical_indicators
from app.core.logger import get_logger

logger = get_logger("api.historical")

router = APIRouter(
    prefix="/historical",
    tags=["historical"]
)

@router.get("/")
def get_historical_prices(
    limit: int = Query(default=100, ge=1, le=1000)
):
    """
    Retrieve historical Bitcoin prices and technical indicators sorted chronologically.
    """
    logger.info(f"Fetching historical prices, limit={limit}")
    # Get 60 more days than limit to allow full indicator window calculation
    fetch_limit = limit + 60
    df = get_historical_data(days=fetch_limit)
    
    if df.empty:
        logger.warning("No historical prices found in database.")
        return []
        
    # Calculate indicators on the fly
    df_with_indicators = add_technical_indicators(df)
    
    # Take only the last 'limit' records and convert to dict
    result_df = df_with_indicators.tail(limit)
    records = result_df.to_dict(orient="records")
    
    # Return chronologically (oldest to newest)
    return records

@router.get("/latest")
def get_latest_price():
    """
    Retrieve the absolute latest historical price record in the database.
    """
    logger.info("Fetching latest historical price record")
    # Fetch latest 60 days to calculate technical indicators correctly for the latest point
    df = get_historical_data(days=60)
    if df.empty:
        raise HTTPException(status_code=404, detail="No historical price data found.")
        
    df_with_indicators = add_technical_indicators(df)
    latest_record = df_with_indicators.iloc[-1].to_dict()
    return latest_record

