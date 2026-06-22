from fastapi import APIRouter, HTTPException
from app.services.supabase_service import get_historical_data, get_predictions, get_latest_insights
from app.services.data_service import add_technical_indicators
from app.core.logger import get_logger

logger = get_logger("api.dashboard")

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"]
)

@router.get("/")
def get_dashboard_data():
    """
    Get consolidated latest price, predictions, and AI insight for the frontend dashboard.
    """
    logger.info("Fetching consolidated dashboard data")
    
    # 1. Fetch latest historical price record (using 60 days to calculate indicators)
    latest_price = None
    df = get_historical_data(days=60)
    if not df.empty:
        try:
            df_indicators = add_technical_indicators(df)
            latest_price = df_indicators.iloc[-1].to_dict()
            # Convert date object to string for JSON serialization
            if 'date' in latest_price:
                latest_price['date'] = str(latest_price['date'])
        except Exception as e:
            logger.error(f"Error preparing technical indicators for dashboard: {e}")
            
    # 2. Fetch latest prediction run (last 4 prediction entries represent the latest run of all models)
    predictions = get_predictions(limit=4)
    for p in predictions:
        if 'prediction_date' in p:
            p['prediction_date'] = str(p['prediction_date'])
        if 'created_at' in p:
            p['created_at'] = str(p['created_at'])
            
    # 3. Fetch latest AI insight record
    insights = get_latest_insights(limit=1)
    latest_insight = insights[0] if insights else None
    if latest_insight:
        if 'created_at' in latest_insight:
            latest_insight['created_at'] = str(latest_insight['created_at'])
            
    return {
        "latest_price": latest_price,
        "predictions": predictions,
        "latest_insight": latest_insight
    }

