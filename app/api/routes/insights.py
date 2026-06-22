from fastapi import APIRouter, HTTPException, Query, status
from typing import List
import pandas as pd

from app.schemas.schemas import AIInsightResponse, CombinedInsightReportResponse
from app.services.supabase_service import get_historical_data, get_latest_insights
from app.services.data_service import add_technical_indicators
from app.models import model_manager
from app.services import gemini_service
from app.core.logger import get_logger

logger = get_logger("api.routes.insights")

router = APIRouter(
    prefix="/insights",
    tags=["insights"]
)

def _get_analysis_context() -> tuple:
    """
    Helper to fetch historical data, compute indicators, run all model forecasts,
    and build a cohesive context dictionary for prompt templates.
    """
    df = get_historical_data(days=90)
    if df.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No historical database records found. Please seed or refresh data first."
        )
    df_indicators = add_technical_indicators(df)
    latest_row = df_indicators.sort_values("date").iloc[-1]
    latest_data_dict = latest_row.to_dict()
    
    # Convert date to string for serialization safety
    if "date" in latest_data_dict:
        latest_data_dict["date"] = str(latest_data_dict["date"])

    # Load ML models and generate forecasts
    model_manager.load_all_models()
    preds = model_manager.run_all_predictions(df_indicators)
    
    # Populate extra fields needed by prompt explanation logic
    preds["latest_close"] = float(latest_row["close"])
    
    return df_indicators, latest_data_dict, preds

@router.get("/summary", response_model=str)
def get_market_summary_insight():
    """
    Generate an AI-driven market analysis based on current daily indicators.
    """
    logger.info("API: Generating AI market summary")
    try:
        _, latest_data_dict, _ = _get_analysis_context()
        insight = gemini_service.generate_market_summary(latest_data_dict)
        return insight
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating market summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate market summary: {str(e)}"
        )

@router.get("/explanation", response_model=str)
def get_prediction_explanation_insight():
    """
    Generate an AI narrative explanation of the ML models' predictions.
    """
    logger.info("API: Generating AI prediction explanation")
    try:
        _, _, preds = _get_analysis_context()
        if preds.get("ensemble_next") is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ML predictions are unavailable. Ensure models are trained first."
            )
        insight = gemini_service.generate_prediction_explanation(preds)
        return insight
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating prediction explanation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate prediction explanation: {str(e)}"
        )

@router.get("/risk", response_model=str)
def get_risk_analysis_insight():
    """
    Generate an AI risk evaluation from technical volatility and model forecasts.
    """
    logger.info("API: Generating AI risk analysis")
    try:
        _, latest_data_dict, preds = _get_analysis_context()
        if preds.get("ensemble_next") is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ML predictions are unavailable. Ensure models are trained first."
            )
        insight = gemini_service.generate_risk_analysis(preds, latest_data_dict)
        return insight
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating risk analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate risk analysis: {str(e)}"
        )

@router.get("/full-report", response_model=CombinedInsightReportResponse)
def get_full_insight_report():
    """
    Trigger and build all 4 AI insights (Market Summary, Explanation, Risk, 7-Day Outlook)
    consolidated into a single response model.
    """
    logger.info("API: Generating full consolidated AI insight report")
    try:
        df_indicators, _, preds = _get_analysis_context()
        if preds.get("ensemble_next") is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ML predictions are unavailable. Ensure models are trained first."
            )
        report = gemini_service.generate_full_report(df_indicators, preds)
        return CombinedInsightReportResponse(**report)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating full AI report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate full AI report: {str(e)}"
        )

@router.get("/history", response_model=List[AIInsightResponse])
def get_insights_history(limit: int = Query(default=10, description="Number of past AI insights to retrieve", ge=1, le=100)):
    """
    Retrieve historical AI insight records stored in the Supabase database.
    """
    logger.info(f"API: Fetching last {limit} AI insights from Supabase")
    try:
        insights = get_latest_insights(limit=limit)
        return insights
    except Exception as e:
        logger.error(f"Error in GET /api/insights/history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch insights history: {str(e)}"
        )
