import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page Configuration for Premium Look and Feel
st.set_page_config(
    page_title="CryptoForecaster - Bitcoin Predictions",
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Styling using CSS injected through st.markdown
st.markdown("""
<style>
    /* Google Fonts import */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap');
    
    /* Global styles */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Headers styling */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        color: #ffffff;
    }
    
    /* Main Background & Gradient Header Card */
    .header-container {
        background: linear-gradient(135deg, #1e1b4b 0%, #311042 50%, #0f172a 100%);
        border-radius: 16px;
        padding: 35px;
        margin-bottom: 25px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    }
    
    /* Card design style */
    .metric-card {
        background: rgba(30, 41, 59, 0.4);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(245, 158, 11, 0.4);
    }
    
    /* Accent text and signals */
    .bullish-text {
        color: #10b981;
        font-weight: 600;
    }
    .bearish-text {
        color: #f43f5e;
        font-weight: 600;
    }
    .neutral-text {
        color: #94a3b8;
        font-weight: 600;
    }
    
    /* Gradient badge */
    .gradient-badge {
        background: linear-gradient(90deg, #f59e0b 0%, #d97706 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 50px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- Navigation / Sidebar -----------------
st.sidebar.markdown("""
<div style="text-align: center; padding: 10px 0;">
    <h2 style="color: #f59e0b; margin-bottom: 5px;">🪙 CryptoForecaster</h2>
    <p style="color: #94a3b8; font-size: 0.85rem;">Ensemble ML & AI Analysis</p>
</div>
<hr style="border-color: rgba(255,255,255,0.1); margin-top: 0; margin-bottom: 20px;" />
""", unsafe_allow_html=True)

api_base_url = st.sidebar.text_input("FastAPI Backend URL", "http://127.0.0.1:8000")

st.sidebar.markdown("### Controls")
if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("""
This dashboard fetches real-time prediction updates from the FastAPI backend services. 
Predictions are updated daily using a combination of **Prophet**, **LSTM**, and **Random Forest** models.
""")

# ----------------- Header Banner -----------------
st.markdown("""
<div class="header-container">
    <div class="gradient-badge">PRO EDITION</div>
    <h1 style="margin: 10px 0 5px 0; font-size: 2.8rem; letter-spacing: -0.5px;">Bitcoin Predictive Analytics Dashboard</h1>
    <p style="color: #cbd5e1; font-size: 1.1rem; max-width: 800px; margin-bottom: 0;">
        Real-time predictive forecasting powered by deep learning ensemble networks and automated market intelligence from Gemini 1.5 Flash.
    </p>
</div>
""", unsafe_allow_html=True)

# ----------------- Dashboard Main Logic -----------------
# Helper function to fetch data
def fetch_data(endpoint):
    try:
        r = requests.get(f"{api_base_url}{endpoint}", timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        st.warning(f"Unable to connect to the backend API at {api_base_url}. Running with simulation data for showcase.")
    return None

dashboard_data = fetch_data("/api/dashboard/")

# Fallback/Simulation Data for rich layout showcase if API is offline
if not dashboard_data:
    # Generate mock dates
    dates = [datetime.now().date() - timedelta(days=i) for i in range(30, 0, -1)]
    prices = [60000 + i * 200 + np.random.randn() * 400 for i in range(30)]
    
    mock_history = []
    for d, p in zip(dates, prices):
        mock_history.append({
            "id": 1,
            "date": d.isoformat(),
            "close_price": p,
            "open_price": p - 100,
            "high_price": p + 300,
            "low_price": p - 200,
            "volume": 25000000000 + np.random.randn() * 500000000,
            "rsi_14": 52.4 + np.random.randn() * 5,
            "macd": 12.4 + np.random.randn() * 2,
            "macd_signal": 10.1 + np.random.randn() * 1.5,
            "created_at": datetime.now().isoformat()
        })
    
    latest_price = mock_history[-1]
    
    latest_prediction = {
        "prediction_date": (datetime.now().date() + timedelta(days=1)).isoformat(),
        "prophet_price": latest_price["close_price"] * 1.012,
        "lstm_price": latest_price["close_price"] * 0.992,
        "sklearn_price": latest_price["close_price"] * 1.008,
        "ensemble_price": latest_price["close_price"] * 1.005,
        "predicted_direction": "UP",
        "trend_7day": "BULLISH",
        "actual_price": None,
        "prediction_error": None,
        "run_date": datetime.now().isoformat()
    }
    
    latest_insight = {
        "prediction_date": latest_prediction["prediction_date"],
        "insight_text": "Bitcoin has shown strong consolidation patterns above key support levels. The RSI resides in neutral territory (~54), while the MACD is exhibiting a slight bullish crossover on the daily chart. The ML ensemble prediction suggests a modest upward target of +0.50% driven by strong weights in the Random Forest lag indicators. Traders should monitor volume trends for institutional breakouts.",
        "sentiment_score": "BULLISH",
        "created_at": datetime.now().isoformat()
    }
else:
    latest_price = dashboard_data.get("latest_price")
    latest_prediction = dashboard_data.get("latest_prediction")
    latest_insight = dashboard_data.get("latest_insight")
    
    historical_prices_res = fetch_data("/api/historical/?limit=100")
    mock_history = historical_prices_res if historical_prices_res else []

# ----------------- Metrics Section -----------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div style="color: #94a3b8; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">BTC Current Price</div>
        <div style="color: #ffffff; font-size: 2.2rem; font-weight: 700; margin: 10px 0;">${latest_price['close_price']:,.2f}</div>
        <div style="font-size: 0.9rem; color: #94a3b8;">As of {latest_price['date']}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    ensemble_price = latest_prediction['ensemble_price']
    curr_price = latest_price['close_price']
    diff = ensemble_price - curr_price
    pct_diff = (diff / curr_price) * 100
    color_class = "bullish-text" if diff > 0 else "bearish-text"
    arrow = "▲" if diff > 0 else "▼"
    
    st.markdown(f"""
    <div class="metric-card">
        <div style="color: #94a3b8; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Tomorrow's Ensemble Prediction</div>
        <div style="color: #ffffff; font-size: 2.2rem; font-weight: 700; margin: 10px 0;">${ensemble_price:,.2f}</div>
        <div style="font-size: 0.9rem;" class="{color_class}">{arrow} {abs(pct_diff):.2f}% (${abs(diff):,.2f})</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    direction = latest_prediction['predicted_direction']
    direction_color = "bullish-text" if direction == "UP" else "bearish-text"
    
    st.markdown(f"""
    <div class="metric-card">
        <div style="color: #94a3b8; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Forecast Direction</div>
        <div class="{direction_color}" style="font-size: 2.2rem; font-weight: 700; margin: 10px 0;">{direction}</div>
        <div style="font-size: 0.9rem; color: #94a3b8;">Targeting close price change</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    trend = latest_prediction['trend_7day']
    trend_color = "bullish-text" if trend == "BULLISH" else "bearish-text" if trend == "BEARISH" else "neutral-text"
    
    st.markdown(f"""
    <div class="metric-card">
        <div style="color: #94a3b8; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">7-Day Strategic Trend</div>
        <div class="{trend_color}" style="font-size: 2.2rem; font-weight: 700; margin: 10px 0;">{trend}</div>
        <div style="font-size: 0.9rem; color: #94a3b8;">Based on mid-range projections</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)

# ----------------- Main Layout -----------------
main_col1, main_col2 = st.columns([2, 1])

with main_col1:
    st.markdown("### 📈 Bitcoin Price Trend & Forecast")
    
    if mock_history:
        # Build DataFrame
        df_hist = pd.DataFrame(mock_history)
        df_hist['date'] = pd.to_datetime(df_hist['date'])
        df_hist = df_hist.sort_values('date')
        
        # Plotting
        fig = go.Figure()
        
        # Historical prices
        fig.add_trace(go.Scatter(
            x=df_hist['date'],
            y=df_hist['close_price'],
            name='Historical Close',
            line=dict(color='#3b82f6', width=2)
        ))
        
        # Forecast point
        pred_date = pd.to_datetime(latest_prediction['prediction_date'])
        fig.add_trace(go.Scatter(
            x=[df_hist['date'].iloc[-1], pred_date],
            y=[df_hist['close_price'].iloc[-1], latest_prediction['ensemble_price']],
            name='Ensemble Forecast',
            line=dict(color='#f59e0b', width=2, dash='dot'),
            marker=dict(size=8, color='#f59e0b')
        ))
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(
                gridcolor='rgba(255,255,255,0.05)',
                color='#94a3b8'
            ),
            yaxis=dict(
                gridcolor='rgba(255,255,255,0.05)',
                color='#94a3b8',
                title="USD ($)"
            ),
            legend=dict(
                font=dict(color='#cbd5e1'),
                bgcolor='rgba(15, 23, 42, 0.8)'
            ),
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No historical charting data available yet.")

with main_col2:
    st.markdown("### 🤖 Gemini Market Intelligence")
    if latest_insight:
        sentiment = latest_insight['sentiment_score']
        s_color = "#10b981" if sentiment == "BULLISH" else "#f43f5e" if sentiment == "BEARISH" else "#94a3b8"
        
        st.markdown(f"""
        <div style="background: rgba(30, 41, 59, 0.3); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 20px; height: 100%;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <span style="color: #cbd5e1; font-weight: 600; font-size: 0.95rem;">AI Insight Report</span>
                <span style="background: {s_color}20; color: {s_color}; padding: 3px 12px; border-radius: 50px; font-size: 0.8rem; font-weight: 700;">
                    {sentiment}
                </span>
            </div>
            <p style="color: #e2e8f0; font-size: 0.92rem; line-height: 1.6; margin-bottom: 15px;">
                {latest_insight['insight_text']}
            </p>
            <div style="font-size: 0.8rem; color: #64748b; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 10px;">
                Generated at {latest_insight.get('created_at', datetime.now().isoformat())}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No AI insights generated yet. Verify your GEMINI_API_KEY config.")

st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 30px 0;' />", unsafe_allow_html=True)

# ----------------- Multi-Model Ensemble details -----------------
st.markdown("### 🧩 ML Ensemble Model Projections")
m_col1, m_col2, m_col3 = st.columns(3)

with m_col1:
    st.markdown(f"""
    <div class="metric-card" style="border-top: 3px solid #6366f1;">
        <h4 style="margin: 0; color: #a5b4fc;">Prophet Model</h4>
        <p style="color: #94a3b8; font-size: 0.85rem; margin-top: 5px;">Time-series decomposition optimized for trend and seasonality</p>
        <div style="font-size: 1.8rem; font-weight: 700; margin: 15px 0;">${latest_prediction['prophet_price']:,.2f}</div>
        <div style="font-size: 0.8rem; color: #64748b;">Weight: 30%</div>
    </div>
    """, unsafe_allow_html=True)

with m_col2:
    st.markdown(f"""
    <div class="metric-card" style="border-top: 3px solid #14b8a6;">
        <h4 style="margin: 0; color: #99f6e4;">LSTM Model</h4>
        <p style="color: #94a3b8; font-size: 0.85rem; margin-top: 5px;">Deep recurrent neural network capturing sequential patterns</p>
        <div style="font-size: 1.8rem; font-weight: 700; margin: 15px 0;">${latest_prediction['lstm_price']:,.2f}</div>
        <div style="font-size: 0.8rem; color: #64748b;">Weight: 40%</div>
    </div>
    """, unsafe_allow_html=True)

with m_col3:
    st.markdown(f"""
    <div class="metric-card" style="border-top: 3px solid #f59e0b;">
        <h4 style="margin: 0; color: #fde047;">Random Forest Regressor</h4>
        <p style="color: #94a3b8; font-size: 0.85rem; margin-top: 5px;">Supervised machine learning trained on lag indicators</p>
        <div style="font-size: 1.8rem; font-weight: 700; margin: 15px 0;">${latest_prediction['sklearn_price']:,.2f}</div>
        <div style="font-size: 0.8rem; color: #64748b;">Weight: 30%</div>
    </div>
    """, unsafe_allow_html=True)
