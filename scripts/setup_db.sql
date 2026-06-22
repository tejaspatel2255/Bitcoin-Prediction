-- SQL schema setup for Supabase (Bitcoin Prediction App)

-- 1. Table for historical Bitcoin prices
CREATE TABLE IF NOT EXISTS btc_historical_data (
    date DATE PRIMARY KEY,
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    volume DOUBLE PRECISION NOT NULL,
    source VARCHAR(50) NOT NULL
);

-- Index for fast queries on date range
CREATE INDEX IF NOT EXISTS idx_btc_historical_data_date ON btc_historical_data(date);

-- 2. Table for machine learning forecasts
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    model_used VARCHAR(100) NOT NULL,
    prediction_type VARCHAR(50) NOT NULL,
    predicted_value DOUBLE PRECISION NOT NULL,
    prediction_date DATE NOT NULL,
    actual_value DOUBLE PRECISION,
    confidence_score DOUBLE PRECISION
);

-- Indexes for prediction date and run date
CREATE INDEX IF NOT EXISTS idx_predictions_date ON predictions(prediction_date);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at);

-- 3. Table for model evaluation metrics
CREATE TABLE IF NOT EXISTS model_metrics (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    mae DOUBLE PRECISION NOT NULL,
    rmse DOUBLE PRECISION NOT NULL,
    mape DOUBLE PRECISION NOT NULL,
    r2 DOUBLE PRECISION NOT NULL,
    evaluated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for evaluated timestamp
CREATE INDEX IF NOT EXISTS idx_model_metrics_evaluated_at ON model_metrics(evaluated_at);

-- 4. Table for AI Gemini Insights
CREATE TABLE IF NOT EXISTS gemini_insights (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    prompt_type VARCHAR(100) NOT NULL,
    response_text TEXT NOT NULL,
    context_json JSONB
);

-- Index for insights creation date
CREATE INDEX IF NOT EXISTS idx_gemini_insights_created_at ON gemini_insights(created_at);
