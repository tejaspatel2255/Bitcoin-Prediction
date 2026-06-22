from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.db_models import HistoricalPrice
from app.schemas.schemas import HistoricalPriceResponse
from app.core.logger import get_logger

logger = get_logger("api.historical")

router = APIRouter(
    prefix="/historical",
    tags=["historical"]
)

@router.get("/", response_model=list[HistoricalPriceResponse])
def get_historical_prices(
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Retrieve historical Bitcoin prices and technical indicators sorted chronologically.
    """
    logger.info(f"Fetching historical prices, limit={limit}")
    prices = db.query(HistoricalPrice).order_by(HistoricalPrice.date.desc()).limit(limit).all()
    # Return reversed to make it chronological (oldest to newest) for charting
    return list(reversed(prices))
