from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional

# ----------------- Historical Prices -----------------

class HistoricalPriceBase(BaseModel):
    date: date
    close_price: float
    open_price: float
    high_price: float
    low_price: float
    volume: float
    rsi_14: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None

class HistoricalPriceCreate(HistoricalPriceBase):
    pass

class HistoricalPriceResponse(HistoricalPriceBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----------------- Predictions -----------------

class PredictionBase(BaseModel):
    prediction_date: date
    prophet_price: float
    lstm_price: float
    sklearn_price: float
    ensemble_price: float
    predicted_direction: str  # 'UP' or 'DOWN'
    trend_7day: str          # 'BULLISH', 'BEARISH', or 'NEUTRAL'
    actual_price: Optional[float] = None
    prediction_error: Optional[float] = None

class PredictionCreate(PredictionBase):
    pass

class PredictionResponse(PredictionBase):
    id: int
    run_date: datetime

    model_config = ConfigDict(from_attributes=True)


# ----------------- AI Insights -----------------

class AIInsightBase(BaseModel):
    prediction_date: date
    insight_text: str
    sentiment_score: str    # 'BULLISH', 'BEARISH', 'NEUTRAL'

class AIInsightCreate(AIInsightBase):
    pass

class AIInsightResponse(AIInsightBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----------------- Composite Dashboard Data -----------------

class DashboardDataResponse(BaseModel):
    latest_price: Optional[HistoricalPriceResponse] = None
    latest_prediction: Optional[PredictionResponse] = None
    latest_insight: Optional[AIInsightResponse] = None
