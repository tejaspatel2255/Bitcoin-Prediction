import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from streamlit_app.utils import safe_api_get
from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.components.html_components import (
    render_topbar,
    prediction_card
)

st.set_page_config(
    page_title="BTC Oracle | Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Global CSS override block for the light-card UI redesign
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* { font-family: 'Inter', sans-serif !important; }

[data-testid="stAppViewContainer"] {
    background: #0F1117;
}
[data-testid="stSidebar"] {
    background: #1A1D27;
    border-right: 1px solid #2A2D3A;
}
[data-testid="stSidebar"] * { color: #CCCCCC; }
[data-testid="block-container"] {
    padding: 1rem 2rem !important;
}
.stButton > button {
    background: #F7931A !important;
    color: #000 !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 20px !important;
    width: 100%;
    transition: background 0.2s;
}
.stButton > button:hover { background: #e07d0a !important; }

div[data-testid="stMetricValue"] {
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    color: #1A1A1A !important;
}
div[data-testid="stMetricLabel"] {
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #888 !important;
}
[data-testid="metric-container"] {
    background: #FFFFFF !important;
    border: 1px solid #E8E8E8 !important;
    border-radius: 12px !important;
    padding: 16px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08) !important;
}
.stRadio > div { flex-direction: row; gap: 6px; }
.stRadio label {
    background: #FFFFFF;
    border: 1px solid #E0E0E0;
    border-radius: 8px;
    padding: 5px 14px;
    color: #555;
    font-size: 13px;
    cursor: pointer;
    font-weight: 500;
}
.stRadio label[data-checked="true"] {
    background: #1A1A1A;
    color: #FFFFFF;
    border-color: #1A1A1A;
}
div[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #E0E0E0;
}
.stSpinner > div { border-top-color: #F7931A !important; }
h1, h2, h3 { color: #FFFFFF !important; font-weight: 600 !important; }
p, span, div { color: inherit; }
.stMarkdown { color: #CCCCCC; }
</style>
""", unsafe_allow_html=True)

# Render Sidebar
render_sidebar()

# Fetch data function
@st.cache_data(ttl=300)
def fetch_dashboard_chart_data(time_range: str) -> pd.DataFrame:
    days_map = {"7D": 7, "30D": 30, "90D": 90, "1Y": 365}
    days = days_map.get(time_range, 90)
    data = safe_api_get(f"/api/data/historical?days={days}")
    if data and isinstance(data, list):
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        return df
    
    # Fallback/Simulation if API offline
    dates = [datetime.now().date() - timedelta(days=i) for i in range(days, 0, -1)]
    close = 68450.0
    records = []
    for i, d in enumerate(dates):
        close = close + np.random.randn() * 700 + (150 if i > (days * 0.6) else -100)
        records.append({
            "date": pd.to_datetime(d),
            "open": close - 250,
            "high": close + 500,
            "low": close - 400,
            "close": close,
            "volume": 25000000000 + np.random.randn() * 2000000000,
            "sma_7": close * 0.99,
            "sma_21": close * 0.985,
            "sma_50": close * 0.975,
            "rsi_14": 45.0 + np.random.randn() * 10,
            "macd": 200.0 + np.random.randn() * 50,
            "macd_signal": 180.0 + np.random.randn() * 40,
            "bb_mid": close,
            "bb_upper": close * 1.04,
            "bb_lower": close * 0.96
        })
    return pd.DataFrame(records)

@st.cache_data(ttl=300)
def fetch_predictions_and_forecast():
    pred = safe_api_get("/api/predict/next-day")
    forecast = safe_api_get("/api/predict/7-day")
    
    if not pred:
        pred = {
            "ensemble_price": 69210.0,
            "lstm_price": 68980.0,
            "rf_price": 69320.0,
            "latest_close": 68450.0,
            "percentage_change": 1.11,
            "prediction_date": str((datetime.now() + timedelta(days=1)).date())
        }
    if not forecast:
        dates = [(datetime.now() + timedelta(days=i)).date() for i in range(1, 8)]
        forecast_list = []
        base_val = 68450.0
        for i, d in enumerate(dates):
            base_val = base_val + (i * 200) + np.random.randn() * 400
            forecast_list.append({
                "date": str(d),
                "yhat": base_val,
                "yhat_lower": base_val - 1200,
                "yhat_upper": base_val + 1200
            })
        forecast = {"forecast": forecast_list}
        
    return pred, forecast

# Top Bar
render_topbar()

# Main Layout split in 2 columns: left (0.65) and right (0.35)
col_left, col_right = st.columns([0.65, 0.35])

with col_left:
    time_range = st.radio("Select range", ["7D", "30D", "90D", "1Y"], index=2, label_visibility="collapsed")
    
    with st.spinner("Loading chart data..."):
        df = fetch_dashboard_chart_data(time_range)
        
    # Plotly Candlestick chart (paper_bgcolor="white", plot_bgcolor="white")
    fig_main = go.Figure()
    
    # Candlestick trace
    fig_main.add_trace(go.Candlestick(
        x=df['date'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='BTC Price',
        increasing_line_color='#4CAF50',
        decreasing_line_color='#F44336'
    ))
    
    # SMA7 (thin gray), SMA21 (thin orange)
    if 'sma_7' in df:
        fig_main.add_trace(go.Scatter(x=df['date'], y=df['sma_7'], name='SMA 7', line=dict(color='#888888', width=1.0)))
    if 'sma_21' in df:
        fig_main.add_trace(go.Scatter(x=df['date'], y=df['sma_21'], name='SMA 21', line=dict(color='#F7931A', width=1.0)))
        
    # Bollinger Bands dashed purple
    if 'bb_upper' in df and 'bb_lower' in df:
        fig_main.add_trace(go.Scatter(x=df['date'], y=df['bb_upper'], name='BB Upper', line=dict(color='#9C27B0', width=1, dash='dash')))
        fig_main.add_trace(go.Scatter(x=df['date'], y=df['bb_lower'], name='BB Lower', line=dict(color='#9C27B0', width=1, dash='dash')))
        
    # Orange volume bars on a secondary y-axis
    fig_main.add_trace(go.Bar(
        x=df['date'],
        y=df['volume'],
        name='Volume',
        marker_color='#F7931A',
        opacity=0.3,
        yaxis='y2'
    ))
    
    fig_main.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#333333", family="Inter, sans-serif"),
        xaxis=dict(gridcolor="#F0F0F0", showgrid=True, zeroline=False),
        yaxis=dict(gridcolor="#F0F0F0", showgrid=True, zeroline=False),
        legend=dict(bgcolor="white", bordercolor="#E8E8E8", borderwidth=1),
        height=420,
        xaxis_rangeslider_visible=False,
        yaxis2=dict(
            title='Volume',
            overlaying='y',
            side='right',
            showgrid=False
        ),
        margin=dict(l=20, r=20, t=20, b=20)
    )
    st.plotly_chart(fig_main, use_container_width=True)

with col_right:
    with st.spinner("Loading predictions..."):
        pred_data, forecast_data = fetch_predictions_and_forecast()
        
    direction_val = "Bullish" if pred_data.get("percentage_change", 0.0) >= 0 else "Bearish"
    prediction_card(
        predicted=pred_data.get("ensemble_price"),
        low=pred_data.get("ensemble_price") * 0.98,
        high=pred_data.get("ensemble_price") * 1.02,
        direction=direction_val,
        confidence=int(pred_data.get("confidence", 78) if "confidence" in pred_data else 78)
    )
    
    st.markdown("<br/>", unsafe_allow_html=True)
    
    # 7-day forecast mini card
    st.markdown("""
    <div style="background:#FFFFFF;border:1px solid #E8E8E8;border-radius:12px;padding:16px;">
        <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:10px;">📅 7-Day Forecast Trend</div>
    """, unsafe_allow_html=True)
    
    if forecast_data and forecast_data.get("forecast"):
        f_df = pd.DataFrame(forecast_data["forecast"])
        f_df["date"] = pd.to_datetime(f_df["date"])
        
        fig_mini = go.Figure()
        # Shaded green confidence band
        fig_mini.add_trace(go.Scatter(
            x=pd.concat([f_df['date'], f_df['date'][::-1]]),
            y=pd.concat([f_df['yhat_upper'], f_df['yhat_lower'][::-1]]),
            fill='toself',
            fillcolor='rgba(76, 175, 80, 0.1)',
            line=dict(color='rgba(255,255,255,0)'),
            showlegend=False
        ))
        # Green trend line
        fig_mini.add_trace(go.Scatter(
            x=f_df['date'],
            y=f_df['yhat'],
            line=dict(color='#4CAF50', width=2),
            showlegend=False
        ))
        fig_mini.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=120,
            margin=dict(l=5, r=5, t=5, b=5)
        )
        st.plotly_chart(fig_mini, use_container_width=True)
        
        target_val = f_df.iloc[-1]["yhat"]
        current_val = pred_data.get("latest_close", 68450.0)
        pct_diff = ((target_val - current_val) / current_val) * 100
        sign = "+" if pct_diff >= 0 else ""
        diff_color = "#4CAF50" if pct_diff >= 0 else "#F44336"
        
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px;">
            <span style="font-size:12px; color:#666;">Target Price</span>
            <span style="font-size:14px; font-weight:700; color:#1A1A1A;">${target_val:,.0f}</span>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:4px;">
            <span style="font-size:12px; color:#666;">Projected Change</span>
            <span style="font-size:12px; font-weight:600; color:{diff_color};">{sign}{pct_diff:.2f}%</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.write("Forecast data not loaded.")
        
    st.markdown("</div>", unsafe_allow_html=True)
