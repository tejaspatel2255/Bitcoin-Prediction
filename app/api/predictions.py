from fastapi import APIRouter, Query, HTTPException
from app.services.supabase_service import get_predictions
from app.services.prediction_service import generate_predictions
from app.core.logger import get_logger

logger = get_logger("api.predictions")

router = APIRouter(
    prefix="/predictions",
    tags=["predictions"]
)

@router.get("/")
def get_prediction_history(
    limit: int = Query(default=30, ge=1, le=100)
):
    """
    Retrieve prediction history sorted by date descending.
    """
    logger.info(f"Fetching predictions list, limit={limit}")
    return get_predictions(limit=limit)

@router.post("/trigger")
def trigger_predictions():
    """
    Manually trigger prediction pipeline execution.
    """
    logger.info("Manually triggered prediction pipeline execution.")
    try:
        res = generate_predictions()
        return res
    except Exception as e:
        logger.error(f"Error executing prediction pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

