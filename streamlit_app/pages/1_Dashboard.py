import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_app.utils import safe_api_get
from streamlit_app.components.sidebar import render_sidebar

st.set_page_config(
    page_title="BTC Oracle | Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject required CSS block at the top of EVERY page
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #0E1117; }
[data-testid="stSidebar"] { background-color: #1A1D27; border-right: 1px solid #F7931A22; }
[data-testid="metric-container"] { background: #1A1D27; border: 1px solid #F7931A22; border-radius: 12px; padding: 16px; }
div[data-testid="stMetricValue"] { color: #F7931A; font-size: 1.6rem; font-weight: 600; }
.stButton > button { background: #F7931A !important; color: #000 !important; border-radius: 8px !important; font-weight: 600 !important; border: none !important; width: 100%; }
.stButton > button:hover { background: #e8820f !important; }
h1, h2, h3 { color: #FFFFFF !important; }
[data-testid="stSidebar"] h1 { color: #F7931A !important; }
.stRadio > div { flex-direction: row; gap: 8px; }
.stRadio label { background: #1A1D27; border: 1px solid #333; border-radius: 8px; padding: 4px 14px; color: #aaa; cursor: pointer; }
.stSelectbox > div > div { background: #1A1D27 !important; border-color: #333 !important; }
div[data-testid="stDataFrame"] { background: #1A1D27; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# Render Sidebar
render_sidebar()

# Title
st.title("📊 Market Analytics Dashboard")

# Time Range Selector (horizontal radio as requested)
range_selection = st.radio("Select Time Range", ["7D", "30D", "90D", "1Y", "All"], index=2)

# Cache data fetch function
@st.cache_data(ttl=300)
def fetch_historical_chart_data(time_range: str) -> pd.DataFrame:
    days_map = {"7D": 7, "30D": 30, "90D": 90, "1Y": 365, "All": 1000}
    days = days_map.get(time_range, 90)
    data = safe_api_get(f"/api/data/historical?days={days}")
    if data and isinstance(data, list):
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        return df
    
    # Fallback/Simulation if API offline
    from datetime import datetime, timedelta
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
            "bb_lower": close * 0.96,
            "volatility": 2.5 + np.random.rand() * 1.5
        })
    return pd.DataFrame(records)

with st.spinner("Loading chart data..."):
    df = fetch_historical_chart_data(range_selection)

# Define standard dark Plotly Template
template = go.layout.Template()
template.layout = go.Layout(
    paper_bgcolor="#0E1117",
    plot_bgcolor="#0E1117",
    font=dict(color="#FFFFFF", family="Inter, sans-serif"),
    xaxis=dict(gridcolor="#1E2130", showgrid=True, zeroline=False),
    yaxis=dict(gridcolor="#1E2130", showgrid=True, zeroline=False),
    legend=dict(bgcolor="#1A1D27", bordercolor="rgba(247, 147, 26, 0.2)", borderwidth=1),
    margin=dict(l=40, r=20, t=40, b=40)
)

col_chart, col_stats = st.columns([4, 1])

with col_chart:
    # ─── 1. Main Candlestick Chart ───
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
    
    # SMA overlays
    if 'sma_7' in df:
        fig_main.add_trace(go.Scatter(x=df['date'], y=df['sma_7'], name='SMA 7', line=dict(color='#FFFFFF', width=1.5)))
    if 'sma_21' in df:
        fig_main.add_trace(go.Scatter(x=df['date'], y=df['sma_21'], name='SMA 21', line=dict(color='#FFEB3B', width=1.5)))
    if 'sma_50' in df:
        fig_main.add_trace(go.Scatter(x=df['date'], y=df['sma_50'], name='SMA 50', line=dict(color='#00E5FF', width=1.5)))
        
    # Bollinger Bands
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
        template=template,
        height=450,
        xaxis_rangeslider_visible=False,
        yaxis2=dict(
            title='Volume',
            overlaying='y',
            side='right',
            showgrid=False
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Watermark annotation "BTC Oracle" in corner (opacity 0.05)
    fig_main.add_annotation(
        text="BTC Oracle",
        xref="paper", yref="paper",
        x=0.05, y=0.95,
        showarrow=False,
        font=dict(size=40, color="rgba(255, 255, 255, 0.05)", family="Inter, sans-serif"),
        align="left"
    )
    
    st.plotly_chart(fig_main, use_container_width=True)
    
    # ─── 2. Subplots (RSI + MACD) ───
    fig_sub = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1)
    
    # RSI subplot
    if 'rsi_14' in df:
        fig_sub.add_trace(go.Scatter(
            x=df['date'], y=df['rsi_14'],
            name='RSI',
            line=dict(color='#F7931A', width=2)
        ), row=1, col=1)
        
        # Red/green dashed threshold lines at 70/30
        fig_sub.add_shape(type="line", x0=df['date'].min(), y0=70, x1=df['date'].max(), y1=70, line=dict(color="#F44336", width=1, dash="dash"), row=1, col=1)
        fig_sub.add_shape(type="line", x0=df['date'].min(), y0=30, x1=df['date'].max(), y1=30, line=dict(color="#4CAF50", width=1, dash="dash"), row=1, col=1)
        
    # MACD subplot
    if 'macd' in df and 'macd_signal' in df:
        macd_hist = df['macd'] - df['macd_signal']
        colors = ['#4CAF50' if val >= 0 else '#F44336' for val in macd_hist]
        
        fig_sub.add_trace(go.Bar(
            x=df['date'], y=macd_hist,
            name='MACD Hist',
            marker_color=colors
        ), row=2, col=1)
        
        fig_sub.add_trace(go.Scatter(
            x=df['date'], y=df['macd_signal'],
            name='Signal Line',
            line=dict(color='#F7931A', width=1.5)
        ), row=2, col=1)
        
    fig_sub.update_layout(
        template=template,
        height=250,
        showlegend=False,
        margin=dict(l=40, r=20, t=10, b=20)
    )
    st.plotly_chart(fig_sub, use_container_width=True)

with col_stats:
    # ─── 3. Right Sidebar Metrics ───
    st.markdown("### 📊 Metrics")
    latest = df.iloc[-1]
    
    rsi_val = latest.get("rsi_14", 50.0)
    macd_sig = latest.get("macd_signal", 0.0)
    
    # Calculate Bollinger Band Width
    if "bb_upper" in latest and "bb_lower" in latest and "bb_mid" in latest:
        bb_width = (latest["bb_upper"] - latest["bb_lower"]) / latest["bb_mid"] * 100
    else:
        bb_width = 8.5
        
    volatility = latest.get("volatility", 2.8)
    vol_usd = latest.get("volume", 28000000000.0)
    
    st.metric(label="Current RSI (14)", value=f"{rsi_val:.1f}")
    st.metric(label="MACD Signal Line", value=f"{macd_sig:,.2f}")
    st.metric(label="Bollinger Band Width", value=f"{bb_width:.2f}%")
    st.metric(label="Volatility Index", value=f"{volatility:.2f}%")
    st.metric(label="24h Volume", value=f"${vol_usd/1e9:.2f}B")
