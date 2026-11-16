# 🪙 Bitcoin Prediction & AI Insight App

> A full-stack, enterprise-grade Bitcoin price forecasting and market intelligence platform powered by an **ensemble Machine Learning pipeline** (Prophet + LSTM + Random Forest), **Supabase/PostgreSQL** for persistence, **OpenRouter AI (Gemini 1.5 Flash)** for automated market reports, an interactive **"What-If" Scenario Simulator**, **Executive PDF Brief Generator**, and a professional **Angular 17** glassmorphism dashboard.

---

## 📸 Architecture Diagram

```text
                                 +------------------------+
                                 |  yfinance / CoinGecko  |
                                 +-----------+------------+
                                             |
                                              v  (Data Ingestion)
                                 +-----------+------------+
                                 |  scripts/seed_data.py  |
                                 +-----------+------------+
                                             |
                                              v  (Upsert Records)
                                 +-----------+------------+
                                 |  Supabase (PostgreSQL) | <--------------------+
                                 +-----------+------------+                      |
                                             |                                   |
                          +-------------------+-------------------+               |
                          |                                       |               |
                          v  (Historical Data)                    v  (Insight Logs|
             +------------+------------+            +------------+------------+   |
             |     scripts/train.py    |            |   gemini_service.py     |   |
             +------------+------------+            +------------+------------+   |
                          |                                       ^               |
                          v  (Saves Model Binary)                 |  (Prompts)    |
             +------------+------------+                          |               |
             |   data/saved_models/    |             +------------+------------+  |
             |   Prophet / LSTM / RF   |             |   OpenRouter API        |  |
             +------------+------------+             |   (Gemini Flash 1.5)    |  |
                          |                          +-------------------------+  |
                          v  (Ensemble Forecast)                                  |
             +------------+------------+                                          |
             |  prediction_service.py  +------------------------------------------+
             +------------+------------+
                          |
                          v  (Reads Data / Forecasts)
             +------------+------------+
             |  FastAPI Backend (API)  |
             +------------+------------+
                          ^
                          |  (JSON API Endpoints / CORS Allowed)
             +------------+------------+
             |    Angular 17 Dashboard | (Theme Toggle | PDF Export | What-If Simulator)
             +-------------------------+
```

---

## 🛠️ Tech Stack & Requirements

### Backend:
*   **Python Version:** `3.11` (strictly required for TensorFlow CPU pre-built binary wheels).
*   **API Framework:** `FastAPI` (REST endpoints, Lifespan loading, background scheduler).
*   **Ensemble ML:** `Prophet` (7-day trend), `scikit-learn` (Random Forest, 60% weight), `TensorFlow CPU` (LSTM sequence neural net, 40% weight).
*   **Database:** `Supabase` PostgreSQL (saves historical data, forecasts, insights, evaluation metrics).
*   **AI Insight Engine:** `OpenRouter API` (OpenAI-compatible Python SDK utilizing `google/gemini-flash-1.5` free tier).

### Frontend (Standalone Single Page Application):
*   **Framework:** `Angular 17` (Standalone Components architecture).
*   **State Management:** Angular Signals for reactive UI state.
*   **Theme & Design:** Dynamic Dark / Light theme switcher with CSS variable design tokens and glassmorphism card components (`backdrop-blur`).
*   **PDF Export Engine:** `jsPDF` for downloading branded Executive Market Intelligence Briefs.
*   **Scenario Simulator:** Interactive "What-If" market simulator allowing users to adjust volume surges, RSI sentiment, and volatility multipliers to view real-time recalculated ensemble predictions.
*   **Charts Library:** `Chart.js` & `ng2-charts` for market trends and gauges.

---

## ⚙️ Step-by-Step Setup Guide

### 1. Virtual Environment Setup
Ensure you have **Python 3.11** installed. Create and activate a virtual environment:

```bash
# Windows (PowerShell)
& "D:\Python Files\Python Installation\python.exe" -m venv venv
.\venv\Scripts\Activate.ps1

# macOS / Linux
python3.11 -m venv venv
source venv/bin/activate
```

### 2. Install Python Dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Setup Supabase Tables
1. Go to [Supabase](https://supabase.com) and create a free project.
2. Open the **SQL Editor** in the Supabase Dashboard.
3. Paste the contents of `scripts/setup_db.sql` and run it to create tables:
    *   `btc_historical_data`
    *   `predictions`
    *   `model_metrics`
    *   `gemini_insights`

### 4. Setup OpenRouter (Gemini) Key
1. Register for a free account at [OpenRouter](https://openrouter.ai).
2. Generate an API key. This key will route to the `google/gemini-flash-1.5` free model tier.

### 5. Configure Environment Variables
Create a `.env` file at the project root based on `.env.example`:
```bash
cp .env.example .env
```
Fill in credentials:
```env
SUPABASE_URL="https://your-project-id.supabase.co"
SUPABASE_KEY="your-anon-public-key"
OPENROUTER_API_KEY="sk-or-v1-your-key-here"
PORT=8000
```

### 6. Install Frontend Dependencies
```bash
cd btc-oracle-frontend
npm install --legacy-peer-deps --no-audit --no-fund
```

---

## 🚀 How to Run the Full App

### Step 1: Seed Historical Data
Fetches 3 years of daily Bitcoin prices and technical indicators (RSI, MACD, Bollinger Bands) and loads them into Supabase.
```bash
python -m scripts.seed_data
```

### Step 2: Train All Models
Fits Prophet, LSTM, and Random Forest models on local CPU and saves binary weights into `data/saved_models/`.
```bash
python -m scripts.train
```

### Step 3: Launch FastAPI Backend
Starts the backend on port 8000:
```bash
python -m uvicorn main:app --reload --port 8000
```

### Step 4: Launch Angular 17 Frontend
Starts the development web server on port 4200:
```bash
# In btc-oracle-frontend/
npm start
```
Open **[http://localhost:4200](http://localhost:4200)** in your browser!

---

## 🧪 Running Tests

Validate data cleaning, technical indicators, ML model predictions, API routes, and database wrappers:
```bash
pytest
```

---

## ⚡ Recent Architecture Upgrades

1. **Interactive "What-If" Scenario Simulator:**
   - Real-time recalculation engine incorporating volume shift, RSI sentiment, and volatility multipliers.
   - Preset buttons (🚀 Bull Surge, 🐻 Bear Selloff, ⚡ High Volatility, 🔄 Reset).
2. **Executive PDF Brief Export:**
   - One-click branded PDF export powered by `jsPDF` capturing market telemetry, 24h targets, and Gemini AI insights.
3. **Glassmorphism & Dual Theme Support:**
   - Smooth Dark/Light mode theme toggle with CSS variable design tokens and glassmorphism blur cards.
