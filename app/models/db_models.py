from sqlalchemy import Column, Integer, Numeric, String, Date, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class HistoricalPrice(Base):
    __tablename__ = "historical_prices"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, nullable=False, index=True)
    close_price = Column(Numeric(12, 2), nullable=False)
    open_price = Column(Numeric(12, 2), nullable=False)
    high_price = Column(Numeric(12, 2), nullable=False)
    low_price = Column(Numeric(12, 2), nullable=False)
    volume = Column(Numeric(20, 2), nullable=False)
    rsi_14 = Column(Numeric(6, 2))
    macd = Column(Numeric(10, 4))
    macd_signal = Column(Numeric(10, 4))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    prediction_date = Column(Date, unique=True, nullable=False, index=True)
    run_date = Column(DateTime(timezone=True), server_default=func.now())
    prophet_price = Column(Numeric(12, 2), nullable=False)
    lstm_price = Column(Numeric(12, 2), nullable=False)
    sklearn_price = Column(Numeric(12, 2), nullable=False)
    ensemble_price = Column(Numeric(12, 2), nullable=False)
    predicted_direction = Column(String(4), nullable=False)  # 'UP' or 'DOWN'
    trend_7day = Column(String(50), nullable=False)          # 'BULLISH', 'BEARISH', or 'NEUTRAL'
    actual_price = Column(Numeric(12, 2))
    prediction_error = Column(Numeric(6, 2))

    # Relationship to AI insights
    insight = relationship("AIInsight", back_populates="prediction", uselist=False, cascade="all, delete-orphan")


class AIInsight(Base):
    __tablename__ = "ai_insights"

    id = Column(Integer, primary_key=True, index=True)
    prediction_date = Column(Date, ForeignKey("predictions.prediction_date", ondelete="CASCADE"), unique=True, nullable=False)
    insight_text = Column(Text, nullable=False)
    sentiment_score = Column(String(20), nullable=False)    # 'BULLISH', 'BEARISH', 'NEUTRAL'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship back to prediction
    prediction = relationship("Prediction", back_populates="insight")
