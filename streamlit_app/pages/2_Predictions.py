import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from streamlit_app.utils import safe_api_get, safe_api_post
from streamlit_app.components.sidebar import render_sidebar, start_live_clock

st.set_page_config(
    page_title="BTC Oracle | ML Predictions",
    page_icon="🔮",
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

# Handle Fresh Prediction Trigger
if st.button("🔮 Run Fresh Prediction"):
    with st.spinner("Calculating ML Ensemble Forecasts..."):
        res = safe_api_get("/api/predict/all")
        if res:
            st.toast("✅ Predictions updated successfully!", icon="🔥")
        else:
            st.toast("⚠️ Failed to update predictions. Using cached values.", icon="⚠️")

# ─── Load Data ───
with st.spinner("Fetching predictions data..."):
    next_day_data = safe_api_get("/api/predict/next-day")
    direction_data = safe_api_get("/api/predict/direction")
    prophet_data = safe_api_get("/api/predict/7-day")
    history_data = safe_api_get("/api/predict/history?limit=30")

# ─── Fallback/Simulation if API offline ───
if not next_day_data:
    st.sidebar.warning("Running in simulation mode for Predictions.")
    latest_close = 68450.00
    ensemble_price = 69210.00
    lstm_price = 68980.00
    rf_price = 69320.00
    
    next_day_data = {
        "prediction_date": str((datetime.now() + timedelta(days=1)).date()),
        "ensemble_price": ensemble_price,
        "lstm_price": lstm_price,
        "rf_price": rf_price,
        "latest_close": latest_close,
        "percentage_change": 1.11
    }
    
    direction_data = {
        "prediction_date": next_day_data["prediction_date"],
        "direction": "UP",
        "confidence": 76.5
    }
    
    # Simulate Prophet forecast
    dates = [(datetime.now() + timedelta(days=i)).date() for i in range(1, 8)]
    forecast_list = []
    base_val = latest_close
    for i, d in enumerate(dates):
        base_val = base_val + (i * 200) + np.random.randn() * 400
        forecast_list.append({
            "date": str(d),
            "yhat": base_val,
            "yhat_lower": base_val - 1800 - (i * 200),
            "yhat_upper": base_val + 1800 + (i * 200)
        })
    prophet_data = {
        "prediction_date": next_day_data["prediction_date"],
        "forecast": forecast_list
    }
    
    # Simulate history data
    hist_dates = [(datetime.now() - timedelta(days=i)).date() for i in range(20, 0, -1)]
    history_list = []
    for i, d in enumerate(hist_dates):
        act_val = 65000 + (i * 250) + np.random.randn() * 600
        pred_val = act_val + np.random.randn() * 500
        history_list.append({
            "prediction_date": str(d),
            "model_used": "ensemble",
            "prediction_type": "price_forecast_1d",
            "predicted_value": pred_val,
            "actual_value": act_val,
            "confidence_score": 0.70 + (np.random.randn() * 0.08)
        })
    history_data = history_list

# Header
st.title("🔮 Ensemble ML Predictions")

# ─── Top Row: 3 Big Prediction Cards ───
p_col1, p_col2, p_col3 = st.columns(3)

with p_col1:
    ens_price = next_day_data.get("ensemble_price", 0.0)
    low_bound = ens_price * 0.985
    high_bound = ens_price * 1.015
    st.markdown(f"""
    <div class="card" style="text-align: center; min-height: 250px;">
        <h4 style="margin: 0; color: #94a3b8;">Next Day Price Target</h4>
        <h1 style="color: #F7931A; font-size: 2.8rem; margin: 15px 0;">${ens_price:,.2f}</h1>
        <p style="color: #94a3b8; font-size: 0.9rem;">
            Confidence Range (95%):<br/>
            <strong>${low_bound:,.2f} - ${high_bound:,.2f}</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

with p_col2:
    direction = direction_data.get("direction", "UP")
    confidence_val = direction_data.get("confidence", 50.0)
    badge = '<span class="badge-up">UP</span>' if direction == "UP" else '<span class="badge-down">DOWN</span>'
    
    st.markdown(f"""
    <div class="card" style="text-align: center; min-height: 250px; padding-bottom: 5px;">
        <h4 style="margin: 0 0 10px 0; color: #94a3b8;">Movement Direction</h4>
        <div style="font-size: 1.5rem; margin-bottom: 10px;">Signal: {badge}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Render mini gauge inside card bounds
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=confidence_val,
        number=dict(suffix="%", font=dict(color="#FFFFFF", size=24)),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor="#FFFFFF"),
            bar=dict(color="#F7931A"),
            bgcolor="#1A1D27",
            bordercolor="rgba(247, 147, 26, 0.2)",
            steps=[
                {"range": [0, 50], "color": "#2A2D3A"},
                {"range": [50, 100], "color": "#3A3D4A"}
            ]
        )
    ))
    fig_gauge.update_layout(
        paper_bgcolor="#1A1D27",
        plot_bgcolor="#1A1D27",
        height=130,
        margin=dict(l=20, r=20, t=10, b=10)
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

with p_col3:
    st.markdown("""
    <div class="card" style="text-align: center; min-height: 250px; padding-bottom: 5px;">
        <h4 style="margin: 0; color: #94a3b8;">7-Day Forecast Trend</h4>
    </div>
    """, unsafe_allow_html=True)
    
    # Render sparkline from Prophet data
    if prophet_data and prophet_data.get("forecast"):
        p_df = pd.DataFrame(prophet_data["forecast"])
        fig_spark = go.Figure()
        fig_spark.add_trace(go.Scatter(
            x=p_df["date"],
            y=p_df["yhat"],
            line=dict(color="#F7931A", width=3),
            hoverinfo="none"
        ))
        fig_spark.update_layout(
            paper_bgcolor="#1A1D27",
            plot_bgcolor="#1A1D27",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=130,
            margin=dict(l=20, r=20, t=10, b=10)
        )
        st.plotly_chart(fig_spark, use_container_width=True)

# ─── Ensemble Breakdown Bar Chart ───
st.markdown("### 📊 Ensemble Model Breakdown")
lst_p = next_day_data.get("lstm_price", 0.0)
rf_p = next_day_data.get("rf_price", 0.0)

fig_breakdown = go.Figure()
fig_breakdown.add_trace(go.Bar(
    x=["LSTM Neural Network (40%)", "Random Forest Lags (60%)", "Ensemble Consensus"],
    y=[lst_p, rf_p, ens_price],
    marker_color=["#00E5FF", "#FFEB3B", "#F7931A"],
    text=[f"${lst_p:,.2f}", f"${rf_p:,.2f}", f"${ens_price:,.2f}"],
    textposition="auto"
))
fig_breakdown.update_layout(
    paper_bgcolor="#0E1117",
    plot_bgcolor="#0E1117",
    font=dict(color="#FFFFFF"),
    xaxis=dict(gridcolor="#2A2D3A", showgrid=True),
    yaxis=dict(gridcolor="#2A2D3A", showgrid=True, range=[min(lst_p, rf_p) * 0.95, max(lst_p, rf_p) * 1.05]),
    legend=dict(bgcolor="#1A1D27", bordercolor="rgba(247, 147, 26, 0.2)"),
    margin=dict(l=20, r=20, t=40, b=20),
    height=320
)
st.plotly_chart(fig_breakdown, use_container_width=True)

# ─── 7-Day Prophet Forecast Chart ───
st.markdown("### 📈 7-Day Shaded Projections (Prophet)")
if prophet_data and prophet_data.get("forecast"):
    p_df = pd.DataFrame(prophet_data["forecast"])
    p_df["date"] = pd.to_datetime(p_df["date"])
    
    fig_prophet = go.Figure()
    
    # Shaded confidence band (orange fill, 20% opacity)
    fig_prophet.add_trace(go.Scatter(
        x=pd.concat([p_df['date'], p_df['date'][::-1]]),
        y=pd.concat([p_df['yhat_upper'], p_df['yhat_lower'][::-1]]),
        fill='toself',
        fillcolor='rgba(247, 147, 26, 0.20)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Confidence Band'
    ))
    
    # Projected line
    fig_prophet.add_trace(go.Scatter(
        x=p_df['date'],
        y=p_df['yhat'],
        name='Trend Line',
        line=dict(color='#F7931A', width=3)
    ))
    
    # Upper/Lower dashed lines
    fig_prophet.add_trace(go.Scatter(x=p_df['date'], y=p_df['yhat_upper'], name='Upper Bound', line=dict(color='#F7931A', width=1, dash='dash')))
    fig_prophet.add_trace(go.Scatter(x=p_df['date'], y=p_df['yhat_lower'], name='Lower Bound', line=dict(color='#F7931A', width=1, dash='dash')))
    
    # Dotted line marking today (today is start of prediction)
    fig_prophet.add_vline(x=p_df['date'].min(), line_width=1.5, line_dash="dot", line_color="#FFFFFF")
    
    fig_prophet.update_layout(
        paper_bgcolor="#0E1117",
        plot_bgcolor="#0E1117",
        font=dict(color="#FFFFFF"),
        xaxis=dict(gridcolor="#2A2D3A", showgrid=True),
        yaxis=dict(gridcolor="#2A2D3A", showgrid=True),
        legend=dict(bgcolor="#1A1D27", bordercolor="rgba(247, 147, 26, 0.2)"),
        margin=dict(l=20, r=20, t=40, b=20),
        height=380
    )
    st.plotly_chart(fig_prophet, use_container_width=True)

# ─── Prediction History Table ───
st.markdown("### 📋 Prediction Accuracy Logs")
if history_data:
    h_df = pd.DataFrame(history_data)
    h_df["prediction_date"] = pd.to_datetime(h_df["prediction_date"]).dt.date
    h_df = h_df.sort_values("prediction_date", ascending=False)
    
    # Compute accuracy percentage column: 100 - absolute percentage error
    h_df["accuracy_pct"] = 100 - (abs(h_df["predicted_value"] - h_df["actual_value"]) / h_df["actual_value"] * 100)
    h_df["accuracy_pct"] = h_df["accuracy_pct"].clip(lower=0.0, upper=100.0)
    
    # Custom display df
    display_df = pd.DataFrame({
        "Date": h_df["prediction_date"],
        "Model Type": h_df["model_used"].str.upper(),
        "Predicted Target": h_df["predicted_value"].map(lambda x: f"${x:,.2f}" if pd.notnull(x) else "N/A"),
        "Actual Price": h_df["actual_value"].map(lambda x: f"${x:,.2f}" if pd.notnull(x) else "N/A"),
        "Accuracy Index": h_df["accuracy_pct"].map(lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A"),
        "Confidence Score": h_df["confidence_score"].map(lambda x: f"{x * 100:.1f}%" if pd.notnull(x) else "N/A")
    })
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

# Update clock
start_live_clock(clock_placeholder)
