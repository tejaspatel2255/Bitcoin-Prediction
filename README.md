# 🪙 Bitcoin Prediction App

> A full-stack, production-quality Bitcoin price forecasting application powered by an **ensemble ML pipeline** (Prophet + LSTM + Random Forest), **Supabase/PostgreSQL** for persistence, **OpenRouter AI (Gemini 1.5 Flash)** for automated market reports, and a **Streamlit** dashboard for visualization.

---

## 📸 Tech Stack

| Layer | Technology |
|---|---|
| **Backend API** | FastAPI + Uvicorn |
| **Frontend Dashboard** | Streamlit + Plotly |
| **ML Models** | Prophet · LSTM (TensorFlow CPU) · Random Forest (scikit-learn) |
| **AI Insights** | OpenRouter AI (google/gemini-flash-1.5) |
| **Database** | Supabase (PostgreSQL) |
| **Data Sources** | yfinance (historical) · CoinGecko (fallback/live price) |
| **Config & Validation** | Pydantic v2 + pydantic-settings |
| **Python Version** | 3.11 (required) |

---

## 📂 Project Structure

```text
bitcoin-prediction/
├── app/
│   ├── api/                  # FastAPI route handlers
│   │   ├── dashboard.py      # GET /api/dashboard/ — consolidated frontend data
│   │   ├── historical.py     # GET /api/historical/ — price & indicator history
│   │   ├── insights.py       # GET/POST /api/insights/ — OpenRouter AI market reports
│   │   └── predictions.py    # GET/POST /api/predictions/ — ML forecast results
│   ├── core/                 # App infrastructure
│   │   ├── config.py         # Pydantic BaseSettings (loads .env)
│   │   ├── database.py       # SQLAlchemy engine + session factory
│   │   └── logger.py         # Structured logger (dev + JSON production mode)
│   ├── models/               # Data layer
│   │   ├── db_models.py      # legacy SQLAlchemy ORM table definitions
│   │   ├── lstm_model.py     # CPU-only TensorFlow LSTM wrapper
│   │   ├── prophet_model.py  # Facebook Prophet model wrapper
│   │   └── rf_model.py       # scikit-learn Random Forest wrapper
│   ├── schemas/              # Pydantic v2 request/response schemas
│   │   ├── __init__.py
│   │   └── schemas.py
│   └── services/             # Business logic layer
│       ├── data_service.py   # yfinance fetch, RSI/MACD, ML feature prep
│       ├── gemini_service.py # OpenRouter AI market insight generator
│       └── prediction_service.py # Ensemble inference + Supabase persistence
├── streamlit_app/
│   └── app.py                # Premium Streamlit frontend dashboard
├── scripts/
│   ├── seed_data.py          # Seeding 3 years of data + indicators into Supabase
│   ├── setup_db.py           # Database connection & health checks
│   ├── train.py              # Full model training pipeline (all 3 models)
│   └── setup_db.sql          # Raw SQL schema for manual Supabase setup
├── data/
│   └── saved_models/         # Trained model artifacts (.keras, .pkl) — gitignored
├── .env.example              # Environment variable template (safe to commit)
├── .gitignore                # Excludes venv, .env, model binaries, OS files
├── main.py                   # FastAPI application entry point
├── requirements.txt          # Pinned Python dependencies
└── README.md
```

---

## ⚙️ Environment Setup

> **Python 3.11 is required.** Python 3.12+ is not compatible with `tensorflow-cpu==2.16.1`.

### 1. Create Virtual Environment with Python 3.11

```powershell
# Windows (PowerShell)
py -3.11 -m venv venv
venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
python3.11 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env   # PowerShell: Copy-Item .env.example .env
```

Edit `.env` and fill in your real credentials:

```env
# Supabase — get from: https://supabase.com/dashboard/project/<your-id>/settings/api
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-public-key
SUPABASE_DB_URL=postgresql://postgres.your-project-id:your-db-password@aws-0-us-east-1.pooler.supabase.com:6543/postgres

# OpenRouter — get from: https://openrouter.ai/keys
OPENROUTER_API_KEY=your-openrouter-api-key
```

### 4. Set Up Database Schema (Supabase)

Run the SQL in `scripts/setup_db.sql` in the **Supabase SQL Editor** to create the required tables (`btc_historical_data`, `predictions`, `model_metrics`, `gemini_insights`).

---

## 🚀 Running the Application

### Step 1 — Seed Historical BTC Data
Fetches 3 years of daily Bitcoin OHLCV data + computes indicators and inserts them into Supabase:
```bash
venv\Scripts\python.exe scripts/seed_data.py
```

### Step 2 — Train ML Models
Trains Prophet, LSTM, and Random Forest models and saves weights to `data/saved_models/`:
```bash
venv\Scripts\python.exe scripts/train.py
```
> ⏱️ This takes ~10–20 minutes on CPU depending on your hardware.

### Step 3 — Start the FastAPI Backend
```bash
venv\Scripts\python.exe main.py
```
- API is live at: **http://127.0.0.1:8000**
- Interactive Swagger docs: **http://127.0.0.1:8000/docs**

### Step 4 — Start the Streamlit Dashboard
```bash
venv\Scripts\streamlit.exe run streamlit_app/app.py
```
- Dashboard is live at: **http://localhost:8501**

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `GET` | `/api/dashboard/` | Consolidated latest price + prediction + insight |
| `GET` | `/api/historical/?limit=100` | Historical OHLCV + indicators |
| `GET` | `/api/predictions/?limit=30` | Historical prediction records |
| `POST` | `/api/predictions/trigger` | Manually trigger the prediction pipeline |
| `GET` | `/api/insights/?limit=10` | Historical AI insight reports |
| `POST` | `/api/insights/trigger` | Generate a fresh OpenRouter AI market insight |

---

## 🧠 ML Model Architecture

### Ensemble Strategy
Final prediction is a **weighted average** of models:

| Model | Weight | Strength |
|---|---|---|
| **LSTM** (TensorFlow CPU) | 40% | Sequential pattern recognition from 60-day lookback window |
| **Random Forest** (scikit-learn) | 60% | Supervised regression on lag features + technical indicators |

*Note: Prophet (Facebook) runs in parallel to generate the long-term 7-day trend narrative, but is excluded from the next-day price ensemble for maximum accuracy.*

### Features Used
- **OHLCV**: Open, High, Low, Close, Volume
- **RSI (14-period)**: Momentum indicator
- **MACD + Signal**: Trend-following indicator
- **SMA (7, 21, 50 day)**: Moving averages
- **EMA (12, 26 day)**: Exponential moving averages
- **Bollinger Bands**: Volatility bands
- **Lag features**: Close/Volume/RSI lagged 1, 3, 7 days

---

## 🔑 Credentials & Keys

| Key | Where to Get It |
|---|---|
| `SUPABASE_URL` | Supabase Dashboard → Project Settings → API |
| `SUPABASE_KEY` | Supabase Dashboard → Project Settings → API → anon/public key |
| `SUPABASE_DB_URL` | Supabase Dashboard → Project Settings → Database → Connection pooler (Transaction mode) |
| `OPENROUTER_API_KEY` | [OpenRouter Dashboard](https://openrouter.ai/keys) |

---

## 🛡️ Important Notes

- **Never commit `.env`** — it is already in `.gitignore`.
- **ML model files** (`.pkl`, `.keras`) are gitignored — they are large and regeneratable via `scripts/train.py`.
- **TensorFlow is CPU-only** — `CUDA_VISIBLE_DEVICES=-1` is set in the LSTM wrapper to prevent any accidental GPU detection.
- The `yfinance` library occasionally fails due to Yahoo Finance rate limits. If `ingest_data.py` fails, wait a few minutes and retry.

---

## 📋 Phase Completion Checklist

- [x] **Phase 1** — Project Setup & Environment ✅
- [ ] **Phase 2** — Data Ingestion Pipeline
- [ ] **Phase 3** — ML Model Training
- [ ] **Phase 4** — FastAPI Backend
- [ ] **Phase 5** — Streamlit Frontend
- [ ] **Phase 6** — Deployment

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
