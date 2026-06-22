from fastapi import APIRouter, HTTPException, Query, status
from typing import List

from app.schemas.schemas import ModelStatusResponse, ModelMetricsResponse, RetrainResponse
from app.services.supabase_service import get_historical_data, get_model_metrics
from app.services.data_service import add_technical_indicators
from app.models import model_manager
from app.core.logger import get_logger

logger = get_logger("api.routes.models")

router = APIRouter(
    prefix="/models",
    tags=["models"]
)

@router.post("/retrain", response_model=RetrainResponse)
def retrain_models():
    """
    Trigger a full retrain of all 3 machine learning models (Prophet, LSTM, Random Forest)
    using the last 3 years of daily historical data.
    """
    logger.info("API: Requesting full model retraining pipeline")
    try:
        # Fetch ~3 years of historical data for training
        df = get_historical_data(days=1095)
        if df.empty or len(df) < 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not enough historical data in database to support training. Need at least 100 rows."
            )
            
        df_indicators = add_technical_indicators(df)
        
        # Run retraining pipeline
        report = model_manager.retrain_all_models(df_indicators)
        return RetrainResponse(
            status="success",
            report=report
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retraining models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model retraining pipeline failed: {str(e)}"
        )

@router.get("/metrics", response_model=List[ModelMetricsResponse])
def get_metrics(limit: int = Query(default=10, description="Retrieve last N model evaluation metrics", ge=1, le=100)):
    """
    Retrieve recent model evaluation metrics from the Supabase database.
    """
    logger.info(f"API: Fetching last {limit} model metrics")
    try:
        metrics = get_model_metrics(limit=limit)
        return metrics
    except Exception as e:
        logger.error(f"Error fetching model metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch model metrics: {str(e)}"
        )

@router.get("/status", response_model=ModelStatusResponse)
def get_model_status():
    """
    Check the current loaded state of all forecasting models in memory.
    """
    logger.info("API: Checking in-memory model status")
    try:
        status_dict = model_manager.load_all_models()
        return ModelStatusResponse(
            prophet=status_dict.get("prophet", "error"),
            lstm=status_dict.get("lstm", "error"),
            random_forest=status_dict.get("random_forest", "error")
        )
    except Exception as e:
        logger.error(f"Error checking model status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check model status: {str(e)}"
        )
