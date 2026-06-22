import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_app.utils import inject_premium_style, safe_api_get, get_api_url

st.set_page_config(
    page_title="Dashboard | Bitcoin Market Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

inject_premium_style()

st.sidebar.markdown("""
<div style="text-align: center; padding: 10px 0;">
    <h2 style="color: #f59e0b; margin-bottom: 5px;">🪙 CryptoForecaster</h2>
    <p style="color: #94a3b8; font-size: 0.85rem;">Ensemble ML & AI Analysis</p>
</div>
<hr style="border-color: rgba(255,255,255,0.1); margin-top: 0; margin-bottom: 20px;" />
""", unsafe_allow_html=True)

# ─── Live Stats Fetching ───
@st.cache_data(ttl=60)
def fetch_live_bitcoin_data() -> dict:
    """Fetch live data from CoinGecko with error fallback."""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true"
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            data = r.json().get("bitcoin", {})
            return {
                "price": float(data.get("usd", 0.0)),
                "market_cap": float(data.get("usd_market_cap", 0.0)),
                "volume_24h": float(data.get("usd_24h_vol", 0.0)),
                "change_24h": float(data.get("usd_24h_change", 0.0))
            }
    except Exception as e:
        st.sidebar.warning(f"CoinGecko API rate limit hit: using fallback price feed.")
    return {}

# ─── Historical DB Data Fetching ───
@st.cache_data(ttl=120)
def fetch_historical_dataset() -> pd.DataFrame:
    """Fetch last 90 days of daily historical records from backend."""
    data = safe_api_get("/api/data/historical?days=90")
    if not data:
        # Fallback simulated dataframe if backend is down
        import numpy as np
        from datetime import datetime, timedelta
        dates = [datetime.now().date() - timedelta(days=i) for i in range(90, 0, -1)]
        close = 60000.0
        records = []
        for i, d in enumerate(dates):
            close = close + np.random.randn() * 600 + (100 if i > 50 else -50)
            records.append({
                "date": str(d),
                "open": close - 200,
                "high": close + 400,
                "low": close - 300,
                "close": close,
                "volume": 28000000000 + np.random.randn() * 1000000000,
                "sma_7": close * 0.99,
                "sma_21": close * 0.98,
                "sma_50": close * 0.97,
                "ema_12": close * 0.995,
                "ema_26": close * 0.985,
                "rsi_14": 52.0 + np.random.randn() * 8,
                "macd": 100.0 + np.random.randn() * 50,
                "macd_signal": 80.0 + np.random.randn() * 40,
                "bb_mid": close,
                "bb_upper": close * 1.05,
                "bb_lower": close * 0.95,
                "source": "simulated"
            })
        return pd.DataFrame(records)
    return pd.DataFrame(data)

# Fetch data
live_stats = fetch_live_bitcoin_data()
df = fetch_historical_dataset()

# If live_stats failed, use last row of df as fallback
if not live_stats and not df.empty:
    last_row = df.iloc[-1]
    live_stats = {
        "price": float(last_row.get("close", 0.0)),
        "market_cap": float(last_row.get("close", 0.0)) * 19700000, # Approx supply
        "volume_24h": float(last_row.get("volume", 0.0)),
        "change_24h": float(last_row.get("daily_return", 0.0)) * 100
    }

# ─── Live Market Banner ───
st.markdown("### 📊 Live Bitcoin (BTC) Price Monitor")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-title">Live Spot Price</div>
        <div class="metric-value">${live_stats.get('price', 0.0):,.2f}</div>
        <div style="color: #94a3b8; font-size: 0.85rem;">BTC/USD Spot</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    change = live_stats.get('change_24h', 0.0)
    delta_class = "metric-delta-positive" if change >= 0 else "metric-delta-negative"
    sign = "+" if change >= 0 else ""
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-title">24h Change</div>
        <div class="metric-value {delta_class}">{sign}{change:.2f}%</div>
        <div style="color: #94a3b8; font-size: 0.85rem;">Daily Return</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-title">24h Trade Volume</div>
        <div class="metric-value">${live_stats.get('volume_24h', 0.0):,.0f}</div>
        <div style="color: #94a3b8; font-size: 0.85rem;">Global Exchanges</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-title">Market Capitalization</div>
        <div class="metric-value">${live_stats.get('market_cap', 0.0):,.0f}</div>
        <div style="color: #94a3b8; font-size: 0.85rem;">Circulating Valuation</div>
    </div>
    """, unsafe_allow_html=True)

# ─── Charts Section ───
st.markdown("### 📈 Interactive Candlestick & Technical Indicators")

# Layout parameters
show_sma = st.sidebar.checkbox("Show Simple Moving Averages (SMA 7/21/50)", value=True)
show_ema = st.sidebar.checkbox("Show Exponential Moving Averages (EMA 12/26)", value=False)
show_bb = st.sidebar.checkbox("Show Bollinger Bands", value=True)

if not df.empty:
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Create subplots: Row 1 = Price + Indicators, Row 2 = Volume, Row 3 = RSI, Row 4 = MACD
    fig = make_subplots(
        rows=4, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.03,
        row_heights=[0.5, 0.15, 0.15, 0.2]
    )
    
    # 1. Main Candlestick Chart
    fig.add_trace(go.Candlestick(
        x=df['date'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='BTC OHLC',
        increasing_line_color='#10b981',
        decreasing_line_color='#ef4444'
    ), row=1, col=1)
    
    # Overlays
    if show_sma:
        fig.add_trace(go.Scatter(x=df['date'], y=df['sma_7'], name='SMA 7', line=dict(color='#818cf8', width=1.5)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['sma_21'], name='SMA 21', line=dict(color='#3b82f6', width=1.5)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['sma_50'], name='SMA 50', line=dict(color='#1d4ed8', width=1.5)), row=1, col=1)
        
    if show_ema:
        fig.add_trace(go.Scatter(x=df['date'], y=df['ema_12'], name='EMA 12', line=dict(color='#fb7185', width=1.5)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['ema_26'], name='EMA 26', line=dict(color='#e11d48', width=1.5)), row=1, col=1)
        
    if show_bb:
        fig.add_trace(go.Scatter(x=df['date'], y=df['bb_upper'], name='BB Upper', line=dict(color='rgba(156, 163, 175, 0.5)', width=1, dash='dash')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['bb_mid'], name='BB Mid', line=dict(color='rgba(156, 163, 175, 0.3)', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['bb_lower'], name='BB Lower', line=dict(color='rgba(156, 163, 175, 0.5)', width=1, dash='dash')), row=1, col=1)

    # 2. Volume Chart
    fig.add_trace(go.Bar(
        x=df['date'],
        y=df['volume'],
        name='Volume',
        marker_color='rgba(148, 163, 184, 0.3)'
    ), row=2, col=1)
    
    # 3. RSI Chart
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['rsi_14'],
        name='RSI (14)',
        line=dict(color='#a855f7', width=2)
    ), row=3, col=1)
    
    # Add RSI thresholds (30, 70)
    fig.add_shape(type="line", x0=df['date'].min(), y0=70, x1=df['date'].max(), y1=70, line=dict(color="#ef4444", width=1, dash="dash"), row=3, col=1)
    fig.add_shape(type="line", x0=df['date'].min(), y0=30, x1=df['date'].max(), y1=30, line=dict(color="#10b981", width=1, dash="dash"), row=3, col=1)

    # 4. MACD Chart
    macd_diff = df['macd'] - df['macd_signal']
    fig.add_trace(go.Scatter(x=df['date'], y=df['macd'], name='MACD', line=dict(color='#f59e0b', width=1.5)), row=4, col=1)
    fig.add_trace(go.Scatter(x=df['date'], y=df['macd_signal'], name='Signal Line', line=dict(color='#3b82f6', width=1.5)), row=4, col=1)
    fig.add_trace(go.Bar(x=df['date'], y=macd_diff, name='MACD Histogram', marker_color='rgba(99, 102, 241, 0.4)'), row=4, col=1)

    # Clean layout styling
    fig.update_layout(
        xaxis_rangeslider_visible=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color='#cbd5e1'),
            bgcolor='rgba(15, 23, 42, 0.6)'
        ),
        height=800
    )
    
    # Grid lines and formatting
    for i in range(1, 5):
        fig.update_yaxes(gridcolor='rgba(255, 255, 255, 0.05)', color='#94a3b8', row=i, col=1)
        fig.update_xaxes(gridcolor='rgba(255, 255, 255, 0.05)', color='#94a3b8', row=i, col=1)
        
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No charting data available. Check system connection.")
