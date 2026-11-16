# 🪙 Bitcoin Prediction & AI Market Intelligence Platform

> A production-grade, full-stack Bitcoin price forecasting and market intelligence platform powered by an **ensemble Machine Learning pipeline** (Prophet + LSTM + Random Forest), **Supabase PostgreSQL** for persistence, **OpenRouter AI (Gemini Flash)** for automated market reports, an interactive **"What-If" Scenario Simulator**, **Executive PDF Brief Generator**, and a high-performance **Angular 17** glassmorphism dashboard.

---

## 🌐 Live Cloud Deployments

| Component | Platform | Live URL |
| :--- | :--- | :--- |
| **Frontend UI** | **Vercel** | [btc-oracle-frontend.vercel.app](https://btc-oracle-frontend.vercel.app) |
| **Backend API** | **Render** | [bitcoin-prediction-backend.onrender.com](https://bitcoin-prediction-backend.onrender.com) |
| **Interactive Docs** | **Swagger UI** | [bitcoin-prediction-backend.onrender.com/docs](https://bitcoin-prediction-backend.onrender.com/docs) |
| **Database** | **Supabase** | `ap-south-1` (Mumbai) PostgreSQL |

---

## 📸 System Architecture

```text
                                  +------------------------+
                                  |  yfinance / CoinGecko  |
                                  +-----------+------------+
                                              |
                                              v  (Data Ingestion / Every 6 Hours)
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
              |  FastAPI Backend (API)  |  (Hosted on Render)
              +------------+------------+
                           ^
                           |  (JSON API Endpoints / CORS Enabled)
              +------------+------------+
              |    Angular 17 Dashboard |  (Hosted on Vercel)
              +-------------------------+  (Dark/Light Themes | PDF Export | What-If Simulator)
```

---

## 🛠️ Tech Stack Breakdown

### Backend (`/app`, `/scripts`, `main.py`)
* **Python Runtime:** `3.11` (locked via `.python-version` for TensorFlow CPU pre-built Linux wheels).
* **API Framework:** `FastAPI` (lifespan startup, dependency injection, CORS middleware).
* **Server:** `Uvicorn` with dynamic port binding (`$PORT`).
* **Ensemble Machine Learning:**
  * **Prophet:** Captures cyclical weekly and yearly Bitcoin price trends and 7-day projections.
  * **Random Forest Regressor & Classifier:** 60% ensemble weight for 24h close price + UP/DOWN direction classification.
  * **TensorFlow CPU LSTM:** 40% ensemble weight using a 2-layer sequence neural net with dropout on 60-day lookback windows.
* **Database & Persistence:** `Supabase` PostgreSQL (saving historical candlesticks, predictions, evaluation metrics, and AI insight logs).
* **AI Market Insights Engine:** `OpenRouter API` (OpenAI-compatible Python SDK calling `google/gemini-flash` for automated market reports).
* **Automated Cron Scheduler:** `APScheduler` (automatically refreshes Bitcoin price candlesticks and calculates technical indicators every 6 hours).

### Frontend (`/btc-oracle-frontend`)
* **Framework:** `Angular 17` with standalone components and reactive Angular Signals.
* **Styling & UI:** Glassmorphism design system (`backdrop-filter: blur`), CSS custom properties, and dynamic Dark/Light theme switching.
* **Visualizations:** `Chart.js` & `ng2-charts` for multi-timeframe price charts, technical indicator overlays, and prediction confidence gauges.
* **Interactive Scenario Simulator:** Real-time recalculation engine incorporating volume surges, volatility multipliers, and RSI sentiment.
* **Executive PDF Brief Generator:** One-click branded PDF compilation via `jsPDF` and `html2canvas`.
* **Routing:** Angular client-side router configured with Vercel SPA rewrites (`vercel.json`).

---

## 📁 Project Directory Structure

```text
Bitcoin-Prediction-main/
├── .python-version                     # Locked Python 3.11.9 for Render builds
├── .env.example                        # Environment variable template
├── .gitignore                          # Production ignore rules (secrets, models, caches)
├── main.py                             # FastAPI application entrypoint & lifespan
├── requirements.txt                    # Production backend Python dependencies
├── render.yaml                         # 1-Click Render Blueprint configuration
├── app/
│   ├── api/routes/                     # REST API route controllers
│   │   ├── data.py                     # Historical BTC data & manual ingestion
│   │   ├── predictions.py              # Next-day, 7-day & ensemble forecast endpoints
│   │   ├── insights.py                 # AI-generated market summaries & risk reports
│   │   └── models.py                   # Model metrics, diagnostics & retraining
│   ├── core/                           # Configuration, logging, database & prompts
│   ├── models/                         # ML Model classes (Prophet, LSTM, Random Forest)
│   ├── schemas/                        # Pydantic request/response validation schemas
│   └── services/                       # Data ingestion, OpenRouter & Supabase services
├── btc-oracle-frontend/                # Angular 17 Standalone Single Page App
│   ├── vercel.json                     # Vercel SPA rewrites & clean routing
│   ├── angular.json                    # Angular CLI build configuration & budgets
│   ├── package.json                    # NPM dependencies & scripts
│   └── src/
│       ├── app/
│       │   ├── pages/                  # Home, Dashboard, Predictions, Insights, Performance
│       │   ├── shared/components/      # Metric cards, model badges, scenario simulator, topbar
│       │   └── core/services/          # Bitcoin, Insight, Model, Prediction & Theme services
│       ├── environments/               # Environment configs (environment.prod.ts)
│       └── styles/                     # Glassmorphism SCSS tokens, cards & typography
├── data/                               # Local data directory & ML model binaries
├── scripts/                            # Operational CLI pipelines (seed, train, setup_db)
└── tests/                              # Pytest / Unittest test suite
```

---

## ☁️ Cloud Deployment Guide

### 1. Database (Supabase)
1. Create a project at [supabase.com](https://supabase.com).
2. Open the **SQL Editor** in the dashboard and run the schema from `scripts/setup_db.sql` to initialize:
   * `btc_historical_data`
   * `predictions`
   * `model_metrics`
   * `gemini_insights`
3. Retrieve your **Project URL** and **`anon` public key** from **Project Settings → API**.

### 2. Backend (Render)
1. Go to [dashboard.render.com](https://dashboard.render.com) and click **New + → Web Service**.
2. Connect your GitHub repository.
3. Configure settings:
   * **Root Directory:** `.` (leave blank)
   * **Runtime:** `Python 3`
   * **Build Command:** `pip install --no-cache-dir -r requirements.txt`
   * **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   * **Plan:** `Free`
4. Add Environment Variables:
   * `PYTHON_VERSION`: `3.11.9`
   * `SUPABASE_URL`: `https://<YOUR-PROJECT-ID>.supabase.co`
   * `SUPABASE_KEY`: `<YOUR-SUPABASE-ANON-KEY>`
   * `OPENROUTER_API_KEY`: `<YOUR-OPENROUTER-KEY>`
   * `ENV`: `production`
   * `DEBUG`: `false`
5. Click **Create Web Service**.

### 3. Frontend (Vercel)
1. In `btc-oracle-frontend/src/environments/environment.prod.ts`, verify your live Render backend URL:
   ```typescript
   export const environment = {
     production: true,
     apiUrl: 'https://bitcoin-prediction-backend.onrender.com',
     coinGeckoUrl: 'https://api.coingecko.com/api/v3'
   };
   ```
2. Go to [vercel.com](https://vercel.com) and import the repository.
3. Configure project settings:
   * **Framework Preset:** `Angular`
   * **Root Directory:** Click Edit and select `btc-oracle-frontend` ⚠️ *(Crucial)*
   * **Build Command:** `npm run build`
   * **Output Directory:** `dist/btc-oracle-frontend`
   * **Install Command:** `npm install --legacy-peer-deps`
4. Click **Deploy**.

---

## 💻 Local Development Setup

### 1. Backend Setup
```bash
# Clone the repository
git clone https://github.com/tejaspatel2255/Bitcoin-Prediction.git
cd Bitcoin-Prediction

# Create and activate virtual environment (Python 3.11 recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1   # On Windows
# source venv/bin/activate    # On macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Fill in your SUPABASE_URL, SUPABASE_KEY, and OPENROUTER_API_KEY

# Seed 3 years of historical Bitcoin data
python -m scripts.seed_data

# Train all machine learning models locally
python -m scripts.train

# Start FastAPI backend
python -m uvicorn main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd btc-oracle-frontend

# Install node dependencies
npm install --legacy-peer-deps

# Start development server
npm start
# Open http://localhost:4200
```

---

## 📡 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Server health check and model loading state |
| `GET` | `/api/data/historical?days=30` | Enriched historical Bitcoin data with indicators |
| `POST` | `/api/data/refresh` | Trigger real-time data ingestion from live APIs |
| `GET` | `/api/predict/next-day` | Next-day target price from Random Forest + LSTM ensemble |
| `GET` | `/api/predict/direction` | UP/DOWN direction prediction and confidence score |
| `GET` | `/api/predict/7-day` | Facebook Prophet 7-day trend forecast |
| `GET` | `/api/predict/all` | Combined payload with all model predictions |
| `GET` | `/api/predict/history?limit=20` | Historical prediction logs stored in database |
| `GET` | `/api/insights/summary` | Gemini AI technical market summary |
| `GET` | `/api/insights/risk` | Gemini AI volatility and risk assessment |
| `GET` | `/api/insights/full-report` | Consolidated 4-section market intelligence report |
| `POST` | `/api/models/retrain` | Trigger full model retraining pipeline |
| `GET` | `/api/models/metrics` | Model evaluation metrics (MAE, RMSE, MAPE, R2) |
| `GET` | `/api/models/diagnostic` | Actual vs. predicted 60-day historical diagnostic data |

---

## 🧪 Testing

Run automated tests to validate data cleaning, technical indicators, ML inference, and Supabase integration:

```bash
pytest
```

---

## 📄 License
This project is open-source under the MIT License.
