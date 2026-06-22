from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.db_models import Prediction
from app.schemas.schemas import PredictionResponse
from app.services.prediction_service import generate_predictions
from app.core.logger import get_logger

logger = get_logger("api.predictions")

router = APIRouter(
    prefix="/predictions",
    tags=["predictions"]
)

@router.get("/", response_model=list[PredictionResponse])
def get_predictions(
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Retrieve prediction history sorted by date descending.
    """
    logger.info(f"Fetching predictions list, limit={limit}")
    predictions = db.query(Prediction).order_by(Prediction.prediction_date.desc()).limit(limit).all()
    return predictions

@router.post("/trigger", response_model=PredictionResponse)
def trigger_predictions(db: Session = Depends(get_db)):
    """
    Manually trigger prediction pipeline execution.
    """
    logger.info("Manually triggered prediction pipeline execution.")
    try:
        res = generate_predictions()
        # Fetch the inserted/updated record from db to return it as schema-compliant response
        prediction = db.query(Prediction).filter(Prediction.prediction_date == res["prediction_date"]).first()
        if not prediction:
            raise HTTPException(status_code=500, detail="Failed to retrieve generated prediction from database.")
        return prediction
    except Exception as e:
        logger.error(f"Error executing prediction pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))
