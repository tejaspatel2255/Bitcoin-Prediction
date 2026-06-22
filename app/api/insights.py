from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.db_models import AIInsight, Prediction, HistoricalPrice
from app.schemas.schemas import AIInsightResponse
from app.services.gemini_service import generate_market_insight
from sqlalchemy.dialects.postgresql import insert
from app.core.logger import get_logger
from datetime import datetime

logger = get_logger("api.insights")

router = APIRouter(
    prefix="/insights",
    tags=["insights"]
)

@router.get("/", response_model=list[AIInsightResponse])
def get_insights(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Retrieve AI market analysis insights sorted by date descending.
    """
    logger.info(f"Fetching AI insights, limit={limit}")
    insights = db.query(AIInsight).order_by(AIInsight.prediction_date.desc()).limit(limit).all()
    return insights

@router.post("/trigger", response_model=AIInsightResponse)
def trigger_insights(db: Session = Depends(get_db)):
    """
    Generate AI Market Insight using Gemini based on the latest available prediction and market price.
    """
    logger.info("Manually triggered AI Insight generation.")
    
    # 1. Fetch latest price
    latest_price = db.query(HistoricalPrice).order_by(HistoricalPrice.date.desc()).first()
    if not latest_price:
        raise HTTPException(status_code=404, detail="No historical price data found. Please ingest price data first.")
        
    # 2. Fetch latest prediction
    latest_prediction = db.query(Prediction).order_by(Prediction.prediction_date.desc()).first()
    if not latest_prediction:
        raise HTTPException(status_code=404, detail="No predictions found. Please trigger predictions first.")
        
    # Prepare dictionaries for Gemini service
    price_dict = {
        "date": latest_price.date,
        "close_price": float(latest_price.close_price),
        "open_price": float(latest_price.open_price),
        "high_price": float(latest_price.high_price),
        "low_price": float(latest_price.low_price),
        "volume": float(latest_price.volume),
        "rsi_14": float(latest_price.rsi_14) if latest_price.rsi_14 else None,
        "macd": float(latest_price.macd) if latest_price.macd else None,
        "macd_signal": float(latest_price.macd_signal) if latest_price.macd_signal else None,
    }
    
    prediction_dict = {
        "prediction_date": latest_prediction.prediction_date,
        "prophet_price": float(latest_prediction.prophet_price),
        "lstm_price": float(latest_prediction.lstm_price),
        "sklearn_price": float(latest_prediction.sklearn_price),
        "ensemble_price": float(latest_prediction.ensemble_price),
        "predicted_direction": latest_prediction.predicted_direction,
        "trend_7day": latest_prediction.trend_7day
    }
    
    # 3. Call Gemini
    insight_res = generate_market_insight(prediction_dict, price_dict)
    
    # 4. Save/Upsert in DB
    try:
        db_data = {
            "prediction_date": latest_prediction.prediction_date,
            "insight_text": insight_res["insight_text"],
            "sentiment_score": insight_res["sentiment_score"]
        }
        
        stmt = insert(AIInsight).values(db_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=["prediction_date"],
            set_={
                "insight_text": stmt.excluded.insight_text,
                "sentiment_score": stmt.excluded.sentiment_score,
                "created_at": datetime.utcnow()
            }
        )
        
        db.execute(stmt)
        db.commit()
        
        saved_insight = db.query(AIInsight).filter(AIInsight.prediction_date == latest_prediction.prediction_date).first()
        return saved_insight
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving AI Insight to database: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save AI Insight: {e}")
