# 🪙 Bitcoin Prediction & AI Insight App

> A full-stack, enterprise-grade Bitcoin price forecasting and market intelligence platform powered by an **ensemble Machine Learning pipeline** (Prophet + LSTM + Random Forest), **Supabase/PostgreSQL** for persistence, **OpenRouter AI (Gemini 1.5 Flash)** for automated market reports, and an interactive **Streamlit** dashboard.

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
                         |  (JSON Endpoints)
            +------------+------------+
            |    Streamlit Dashboard  |
            +-------------------------+
```

---

## 🛠️ Tech Stack & Requirements

*   **Python Version:** `3.11` (strictly required; TensorFlow CPU pins fail on 3.12+).
*   **Backend framework:** `FastAPI` (REST endpoints, Lifespan loading, background scheduler).
*   **Frontend dashboard:** `Streamlit` (Interactive multi-page charts, Plotly indicators).
*   **Ensemble ML:** `Prophet` (7-day trend), `scikit-learn` (Random Forest, 60% weight), `TensorFlow CPU` (LSTM sequence neural net, 40% weight).
*   **Database:** `Supabase` PostgreSQL (saves historical data, forecasts, insights, evaluation metrics).
*   **AI Insight Engine:** `OpenRouter API` (OpenAI-compatible python SDK utilizing `google/gemini-flash-1.5` free tier).

---

## ⚙️ Step-by-Step Setup Guide

### 1. Virtual Environment Setup
Ensure you have Python 3.11 installed. Create and activate a virtual environment:

```bash
# Windows
py -3.11 -m venv venv
venv\Scripts\Activate.ps1

# macOS / Linux
python3.11 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies & Build Tools
Install required packages and pins:
```bash
pip install --upgrade pip
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
2. Go to keys page and generate an API key. This key will route to the `google/gemini-flash-1.5` free model tier.

### 5. Configure Environment variables
Create a `.env` file at the project root based on `.env.example`:
```bash
cp .env.example .env
```
Fill in the credentials:
```env
SUPABASE_URL="https://your-project-id.supabase.co"
SUPABASE_KEY="your-anon-public-key"
OPENROUTER_API_KEY="sk-or-v1-your-key-here"
```

---

## 📡 Environment Variables Reference

| Variable | Scope | Purpose |
|---|---|---|
| `SUPABASE_URL` | Supabase API | The web endpoint for your Supabase project instance |
| `SUPABASE_KEY` | Supabase API | The anonymous API key for executing SELECT/INSERT commands |
| `OPENROUTER_API_KEY` | AI insights | The API token used to request predictions and analysis reports |
| `PORT` | API Port | Port number to bind FastAPI to (defaults to `8000`) |

---

## 🚀 How to Run the Full App

Using the provided **Makefile** (on Windows or UNIX shell):

### Step 1: Seed Historical Data
Fetches 3 years of daily Bitcoin prices and technical indicators (RSI, MACD, Bollinger Bands) and loads them into Supabase.
```bash
make seed
```

### Step 2: Train All Models
Fits Prophet, LSTM, and Random Forest models on local CPU and saves binary weights into `data/saved_models/`.
```bash
make train
```

### Step 3: Launch Frontend & Backend Concurrently
Launches the FastAPI backend and Streamlit dashboard in concurrent windows:
```bash
make run-all
```
*   **FastAPI Backend:** Live at `http://127.0.0.1:8000` (docs: `/docs`)
*   **Streamlit UI Dashboard:** Live at `http://127.0.0.1:8501`

---

## 🧪 Running Tests

A comprehensive unit test suite has been built to validate data cleaning, technical indicators, ML model predictions, API routes, and database wrappers:
```bash
make test
```

---

## 🛡️ Critical Technical Guards

1.  **CPU-Only Enforcement:** In `app/models/lstm_model.py`, `CUDA_VISIBLE_DEVICES` is set to `"-1"` to prevent execution thread conflicts with local GPU hardware.
2.  **Robust Error Handling:** All database operations are wrapped in safe exception handling blocks returning standard fallback data when database credentials are not present.
3.  **LLM Rate Limit Handling:** Insights requests to OpenRouter contain automatic exponential backoff loops (`2s`, `4s`, `8s`) for robust rate-limit handling.
