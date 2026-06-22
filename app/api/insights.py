from fastapi import APIRouter, HTTPException, Query
from app.services.supabase_service import get_latest_insights, insert_gemini_insight, get_historical_data, get_predictions
from app.services.data_service import add_technical_indicators
from app.services.gemini_service import generate_market_insight
from app.core.logger import get_logger
from datetime import datetime

logger = get_logger("api.insights")

router = APIRouter(
    prefix="/insights",
    tags=["insights"]
)

@router.get("/")
def get_insights(
    limit: int = Query(default=10, ge=1, le=50)
):
    """
    Retrieve AI market analysis insights sorted by date descending.
    """
    logger.info(f"Fetching AI insights, limit={limit}")
    return get_latest_insights(limit=limit)

@router.post("/trigger")
def trigger_insights():
    """
    Generate AI Market Insight using Gemini based on the latest available prediction and market price.
    """
    logger.info("Manually triggered AI Insight generation.")
    
    # 1. Fetch latest price (using 60 days to compute indicators correctly)
    df_hist = get_historical_data(days=60)
    if df_hist.empty:
        raise HTTPException(status_code=404, detail="No historical price data found. Please ingest price data first.")
        
    df_indicators = add_technical_indicators(df_hist)
    latest_price = df_indicators.iloc[-1]
    
    # Prepare price dict for Gemini
    price_dict = {
        "date": str(latest_price["date"]),
        "close_price": float(latest_price["close"]),
        "open_price": float(latest_price["open"]),
        "high_price": float(latest_price["high"]),
        "low_price": float(latest_price["low"]),
        "volume": float(latest_price["volume"]),
        "rsi_14": float(latest_price["rsi_14"]),
        "macd": float(latest_price["macd"]),
        "macd_signal": float(latest_price["macd_signal"])
    }
    
    # 2. Fetch latest prediction run (last 4 prediction entries in DB represent the latest run of 4 models)
    preds = get_predictions(limit=4)
    if not preds:
        raise HTTPException(status_code=404, detail="No predictions found. Please run the predictions pipeline first.")
        
    # Map predictions by model name
    pred_map = {p["model_used"]: float(p["predicted_value"]) for p in preds}
    prediction_date = preds[0]["prediction_date"]
    
    # Check that ensemble is present
    if "ensemble" not in pred_map:
        raise HTTPException(status_code=400, detail="Latest predictions run is incomplete (missing ensemble).")
        
    ensemble_val = pred_map["ensemble"]
    latest_close = price_dict["close_price"]
    
    prediction_dict = {
        "prediction_date": str(prediction_date),
        "prophet_price": pred_map.get("prophet", ensemble_val),
        "lstm_price": pred_map.get("lstm", ensemble_val),
        "sklearn_price": pred_map.get("random_forest", ensemble_val),
        "ensemble_price": ensemble_val,
        "predicted_direction": "UP" if ensemble_val > latest_close else "DOWN",
        "trend_7day": "BULLISH" if ensemble_val > latest_close * 1.015 else ("BEARISH" if ensemble_val < latest_close * 0.985 else "NEUTRAL")
    }
    
    # 3. Call Gemini API
    insight_res = generate_market_insight(prediction_dict, price_dict)
    
    # 4. Save to Supabase gemini_insights table
    insight_dict = {
        "prompt_type": "standard_daily_market_report",
        "response_text": insight_res["insight_text"],
        "context_json": {
            "prediction_date": str(prediction_date),
            "sentiment_score": insight_res["sentiment_score"],
            "latest_close": latest_close,
            "predicted_close": ensemble_val,
            "predicted_direction": prediction_dict["predicted_direction"],
            "trend_7day": prediction_dict["trend_7day"]
        }
    }
    
    res = insert_gemini_insight(insight_dict)
    if res.get("status") == "success":
        return res.get("data")
    else:
        raise HTTPException(status_code=500, detail=f"Failed to save AI Insight: {res.get('message')}")

