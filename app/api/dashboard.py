from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.db_models import HistoricalPrice, Prediction, AIInsight
from app.schemas.schemas import DashboardDataResponse
from app.core.logger import get_logger

logger = get_logger("api.dashboard")

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"]
)

@router.get("/", response_model=DashboardDataResponse)
def get_dashboard_data(db: Session = Depends(get_db)):
    """
    Get consolidated latest price, prediction, and AI insight for the frontend dashboard.
    """
    logger.info("Fetching consolidated dashboard data")
    
    # 1. Fetch latest historical price record
    latest_price = db.query(HistoricalPrice).order_by(HistoricalPrice.date.desc()).first()
    
    # 2. Fetch latest prediction record
    latest_prediction = db.query(Prediction).order_by(Prediction.prediction_date.desc()).first()
    
    # 3. Fetch latest AI insight record
    latest_insight = None
    if latest_prediction:
        latest_insight = db.query(AIInsight).filter(AIInsight.prediction_date == latest_prediction.prediction_date).first()
    
    return DashboardDataResponse(
        latest_price=latest_price,
        latest_prediction=latest_prediction,
        latest_insight=latest_insight
    )
