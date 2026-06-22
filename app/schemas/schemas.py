from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List, Dict, Any

# ─── Data Schemas ─────────────────────────────────────────────────────────────

class HistoricalDataResponse(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str
    
    # Technical Indicators (Optional in case indicator calculation is in progress or failed)
    sma_7: Optional[float] = None
    sma_21: Optional[float] = None
    sma_50: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    rsi_14: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    bb_mid: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_lower: Optional[float] = None
    daily_return: Optional[float] = None
    log_return: Optional[float] = None
    volume_sma: Optional[float] = None
    volatility: Optional[float] = None

    class Config:
        from_attributes = True


class RefreshDataResponse(BaseModel):
    status: str
    message: str
    rows_added: int


# ─── Prediction Schemas ───────────────────────────────────────────────────────

class PredictionRecordResponse(BaseModel):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    model_used: str
    prediction_type: str
    predicted_value: float
    prediction_date: date
    actual_value: Optional[float] = None
    confidence_score: Optional[float] = None

    class Config:
        from_attributes = True


class NextDayPredictionResponse(BaseModel):
    prediction_date: date
    ensemble_price: float
    lstm_price: float
    rf_price: float
    latest_close: float
    percentage_change: float


class NextDayDirectionResponse(BaseModel):
    prediction_date: date
    direction: str  # 'UP' or 'DOWN'
    confidence: float  # Confidence percentage (e.g. 90.0)


class ProphetForecastItem(BaseModel):
    date: date
    yhat: float
    yhat_lower: float
    yhat_upper: float


class ProphetForecastResponse(BaseModel):
    prediction_date: date
    forecast: List[ProphetForecastItem]


class AllPredictionsResponse(BaseModel):
    prediction_date: date
    prophet_price: Optional[float] = None
    lstm_price: Optional[float] = None
    rf_price: Optional[float] = None
    rf_direction: Optional[str] = None
    ensemble_price: Optional[float] = None


# ─── AI Insight Schemas ────────────────────────────────────────────────────────

class AIInsightResponse(BaseModel):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    prompt_type: str
    response_text: str
    context_json: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class CombinedInsightReportResponse(BaseModel):
    market_summary: str
    prediction_explanation: str
    risk_analysis: str
    seven_day_outlook: str


# ─── Model Management Schemas ─────────────────────────────────────────────────

class ModelMetricsResponse(BaseModel):
    id: Optional[int] = None
    model_name: str
    mae: float
    rmse: float
    mape: float
    r2: float
    evaluated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ModelStatusResponse(BaseModel):
    prophet: str
    lstm: str
    random_forest: str


class RetrainResponse(BaseModel):
    status: str
    report: Dict[str, Any]
