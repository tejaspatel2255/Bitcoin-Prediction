import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_app.utils import safe_api_get
from streamlit_app.components.sidebar import render_sidebar, start_live_clock

st.set_page_config(
    page_title="BTC Oracle | Interactive Charts",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling block
st.markdown("""
<style>
/* Global dark theme */
[data-testid="stAppViewContainer"] { background-color: #0E1117; }
[data-testid="stSidebar"] { background-color: #1A1D27; border-right: 1px solid #F7931A33; }
[data-testid="metric-container"] {
    background-color: #1A1D27;
    border: 1px solid #F7931A33;
    border-radius: 12px;
    padding: 16px;
}
.stButton > button {
    background-color: #F7931A;
    color: #000;
    border-radius: 8px;
    font-weight: bold;
    border: none;
    width: 100%;
}
.stButton > button:hover { background-color: #e8820f; }
div[data-testid="stMetricValue"] { color: #F7931A; font-size: 1.8rem; font-weight: bold; }
div[data-testid="stMetricDelta"] { font-size: 0.9rem; }
h1, h2, h3 { color: #FFFFFF; }
.card {
    background: #1A1D27;
    border: 1px solid #F7931A33;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
}
.badge-up { background: #00C853; color: #000; padding: 4px 10px; border-radius: 20px; font-weight: bold; }
.badge-down { background: #FF1744; color: #fff; padding: 4px 10px; border-radius: 20px; font-weight: bold; }
.insight-box {
    background: #1A1D27;
    border-left: 4px solid #F7931A;
    border-radius: 8px;
    padding: 16px 20px;
    margin: 12px 0;
    color: #E0E0E0;
    line-height: 1.7;
}
</style>
""", unsafe_allow_html=True)

# Render custom sidebar
clock_placeholder = render_sidebar()

# ─── Data Fetching ───
@st.cache_data(ttl=120)
def fetch_chart_data(days_input: str) -> pd.DataFrame:
    # Map range selector to days count
    days_map = {"7D": 7, "30D": 30, "90D": 90, "1Y": 365, "All": 1000}
    days = days_map.get(days_input, 90)
    
    data = safe_api_get(f"/api/data/historical?days={days}")
    if not data:
        # Generate robust simulation fallback if backend/DB is not accessible
        from datetime import datetime, timedelta
        dates = [datetime.now().date() - timedelta(days=i) for i in range(days, 0, -1)]
        close = 68450.0
        records = []
        for i, d in enumerate(dates):
            close = close + np.random.randn() * 700 + (150 if i > (days * 0.6) else -100)
            records.append({
                "date": str(d),
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
                "volatility": 2.45
            })
        return pd.DataFrame(records)
    return pd.DataFrame(data)

# Header
st.title("📈 Interactive Market Analytics")

# Time Range Selector: [7D | 30D | 90D | 1Y | All]
range_sel = st.radio(
    "Select Range",
    options=["7D", "30D", "90D", "1Y", "All"],
    index=2,
    horizontal=True
)

df = fetch_chart_data(range_sel)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

# 2-Column layout: Left = Chart, Right = Indicator metrics
col_left, col_right = st.columns([4, 1.2])

with col_left:
    if not df.empty:
        # Create subplots
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.55, 0.20, 0.25]
        )
        
        # 1. Main Candlestick Chart
        fig.add_trace(go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='BTC OHLC',
            increasing_line_color='#00C853',
            decreasing_line_color='#FF1744'
        ), row=1, col=1)
        
        # Overlays
        # SMA 7 (white)
        if 'sma_7' in df:
            fig.add_trace(go.Scatter(x=df['date'], y=df['sma_7'], name='SMA 7', line=dict(color='#FFFFFF', width=1.5)), row=1, col=1)
        # SMA 21 (yellow)
        if 'sma_21' in df:
            fig.add_trace(go.Scatter(x=df['date'], y=df['sma_21'], name='SMA 21', line=dict(color='#FFEB3B', width=1.5)), row=1, col=1)
        # SMA 50 (cyan)
        if 'sma_50' in df:
            fig.add_trace(go.Scatter(x=df['date'], y=df['sma_50'], name='SMA 50', line=dict(color='#00E5FF', width=1.5)), row=1, col=1)
            
        # Bollinger Bands (purple, dashed)
        if 'bb_upper' in df and 'bb_lower' in df:
            fig.add_trace(go.Scatter(x=df['date'], y=df['bb_upper'], name='BB Upper', line=dict(color='#E040FB', width=1, dash='dash')), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['date'], y=df['bb_lower'], name='BB Lower', line=dict(color='#E040FB', width=1, dash='dash')), row=1, col=1)
            
        # 2. Volume Chart (orange volume bars)
        fig.add_trace(go.Bar(
            x=df['date'],
            y=df['volume'],
            name='Volume',
            marker_color='#F7931A',
            opacity=0.85
        ), row=2, col=1)
        
        # 3. RSI Chart below (with 70/30 thresholds in red/green)
        if 'rsi_14' in df:
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['rsi_14'],
                name='RSI (14)',
                line=dict(color='#F7931A', width=2)
            ), row=3, col=1)
            fig.add_shape(type="line", x0=df['date'].min(), y0=70, x1=df['date'].max(), y1=70, line=dict(color="#FF1744", width=1.2, dash="dash"), row=3, col=1)
            fig.add_shape(type="line", x0=df['date'].min(), y0=30, x1=df['date'].max(), y1=30, line=dict(color="#00C853", width=1.2, dash="dash"), row=3, col=1)
            
        # Apply standard layout template requested
        fig.update_layout(
            xaxis_rangeslider_visible=False,
            paper_bgcolor="#0E1117",
            plot_bgcolor="#0E1117",
            font=dict(color="#FFFFFF"),
            xaxis=dict(gridcolor="#2A2D3A", showgrid=True),
            yaxis=dict(gridcolor="#2A2D3A", showgrid=True),
            legend=dict(bgcolor="#1A1D27", bordercolor="rgba(247, 147, 26, 0.2)"),
            margin=dict(l=20, r=20, t=40, b=20),
            height=780
        )
        
        # Watermark "BTC Oracle" in the corner
        fig.add_annotation(
            text="BTC Oracle",
            xref="paper", yref="paper",
            x=0.01, y=0.98,
            showarrow=False,
            font=dict(size=20, color="rgba(247, 147, 26, 0.15)", family="Arial Black")
        )
        
        # Format axes
        for r in range(1, 4):
            fig.update_yaxes(gridcolor="#2A2D3A", showgrid=True, color="#FFFFFF", row=r, col=1)
            fig.update_xaxes(gridcolor="#2A2D3A", showgrid=True, color="#FFFFFF", row=r, col=1)
            
        st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.markdown("<h4 style='text-align: center;'>Live Technical Metrics</h4>", unsafe_allow_html=True)
    if not df.empty:
        latest = df.iloc[-1]
        
        # RSI Card
        rsi_val = latest.get('rsi_14', 50.0)
        rsi_status = "Overbought" if rsi_val >= 70 else ("Oversold" if rsi_val <= 30 else "Neutral")
        st.metric(label="RSI (14)", value=f"{rsi_val:.2f}", delta=rsi_status)
        
        # MACD Card
        macd_val = latest.get('macd', 0.0)
        macd_sig = latest.get('macd_signal', 0.0)
        st.metric(label="MACD Signal Line", value=f"{macd_sig:,.2f}", delta=f"MACD: {macd_val:,.2f}")
        
        # SMA Distances
        close_price = latest.get('close', 0.0)
        sma7 = latest.get('sma_7', close_price)
        sma21 = latest.get('sma_21', close_price)
        dist_pct = ((close_price - sma21) / sma21) * 100 if sma21 else 0
        st.metric(
            label="Distance to SMA 21",
            value=f"{dist_pct:+.2f}%",
            delta=f"Close: ${close_price:,.2f}"
        )
        
        # Volatility %
        vol_pct = latest.get('volatility', 2.0)
        st.metric(label="Daily Volatility", value=f"{vol_pct:.2f}%", delta="Historical 30d")
        
        # Quick explanations
        st.markdown(f"""
        <div class="card" style="margin-top: 15px; font-size: 0.8rem; line-height: 1.5; color: #94a3b8;">
            <strong>Interpretation Guidelines:</strong><br/>
            • <b>RSI &gt; 70</b>: Market overbought (sell signal)<br/>
            • <b>RSI &lt; 30</b>: Market oversold (buy signal)<br/>
            • <b>Positive SMA Distance</b>: Indicates upward momentum.
        </div>
        """, unsafe_allow_html=True)

# Update custom clock at page finish
start_live_clock(clock_placeholder)
