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
    prediction_card,
    section_label
)

st.set_page_config(
    page_title="BTC Oracle | Predictions",
    page_icon="🔮",
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

/* Custom light-card wrapper */
.card-wrapper {
    background: #FFFFFF;
    border: 1px solid #E8E8E8;
    border-radius: 12px;
    padding: 18px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    min-height: 250px;
}
</style>
""", unsafe_allow_html=True)

# Render Sidebar
render_sidebar()

# ─── Load Data ───
with st.spinner("Loading predictions..."):
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
        pred_val = act_val + np.random.randn() * 400
        history_list.append({
            "prediction_date": str(d),
            "model_used": "ensemble",
            "prediction_type": "price_forecast_1d",
            "predicted_value": pred_val,
            "actual_value": act_val,
            "confidence_score": 0.70 + (np.random.randn() * 0.08)
        })
    history_data = history_list

# Top Bar
render_topbar()

# ─── Top 3 Columns ───
col_top1, col_top2, col_top3 = st.columns(3)

with col_top1:
    direction_val = "Bullish" if next_day_data.get("percentage_change", 0.0) >= 0 else "Bearish"
    prediction_card(
        predicted=next_day_data.get("ensemble_price"),
        low=next_day_data.get("ensemble_price") * 0.98,
        high=next_day_data.get("ensemble_price") * 1.02,
        direction=direction_val,
        confidence=int(direction_data.get("confidence", 76.5))
    )

with col_top2:
    st.markdown("""
    <div class="card-wrapper" style="text-align: center; padding-bottom: 0;">
        <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:10px;">📈 Direction Confidence</div>
    """, unsafe_allow_html=True)
    
    conf_val = direction_data.get("confidence", 50.0)
    gauge_col = "#4CAF50" if direction_val == "Bullish" else "#F44336"
    
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=conf_val,
        number=dict(suffix="%", font=dict(color="#1A1A1A", size=22)),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor="#333"),
            bar=dict(color=gauge_col),
            bgcolor="white",
            bordercolor="#E8E8E8",
            steps=[
                {"range": [0, 50], "color": "#F9F9F9"},
                {"range": [50, 100], "color": "#F0F0F0"}
            ]
        )
    ))
    fig_gauge.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        height=140,
        margin=dict(l=10, r=10, t=10, b=10)
    )
    st.plotly_chart(fig_gauge, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_top3:
    st.markdown("""
    <div class="card-wrapper" style="text-align: center; padding-bottom: 0;">
        <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:10px;">📅 7-Day Trend</div>
    """, unsafe_allow_html=True)
    
    # Sparkline chart from Prophet
    if prophet_data and prophet_data.get("forecast"):
        p_df = pd.DataFrame(prophet_data["forecast"])
        fig_sp = go.Figure()
        fig_sp.add_trace(go.Scatter(
            x=p_df["date"],
            y=p_df["yhat"],
            line=dict(color="#F7931A", width=3),
            hoverinfo="none"
        ))
        fig_sp.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=140,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig_sp, use_container_width=True)
    else:
        st.write("Trend data unavailable")
        
    st.markdown("</div>", unsafe_allow_html=True)

# Section Label: Predictions
section_label("🔮", "Predictions")

# Ensemble Breakdown horizontal bar chart (white bg, orange bars)
lstm_p = next_day_data.get("lstm_price", 0.0)
rf_p = next_day_data.get("rf_price", 0.0)
ens_p = next_day_data.get("ensemble_price", 0.0)

fig_break = go.Figure()
fig_break.add_trace(go.Bar(
    y=["LSTM Neural Net", "Random Forest Lags", "Ensemble Consensus"],
    x=[lstm_p, rf_p, ens_p],
    orientation="h",
    marker_color="#F7931A",
    text=[f"${lstm_p:,.2f}", f"${rf_p:,.2f}", f"${ens_p:,.2f}"],
    textposition="auto"
))
fig_break.update_layout(
    paper_bgcolor="white",
    plot_bgcolor="white",
    font=dict(color="#333333", family="Inter, sans-serif"),
    xaxis=dict(gridcolor="#F0F0F0", showgrid=True, title="Forecast Price ($)", range=[min(lstm_p, rf_p, ens_p)*0.98, max(lstm_p, rf_p, ens_p)*1.02]),
    yaxis=dict(showgrid=False),
    height=250,
    margin=dict(l=40, r=20, t=20, b=40)
)
st.plotly_chart(fig_break, use_container_width=True)

# 7-day Prophet forecast chart (white bg)
if prophet_data and prophet_data.get("forecast"):
    p_df = pd.DataFrame(prophet_data["forecast"])
    p_df["date"] = pd.to_datetime(p_df["date"])
    
    fig_pr = go.Figure()
    
    # Shaded confidence band (opacity 15%, orange)
    fig_pr.add_trace(go.Scatter(
        x=pd.concat([p_df['date'], p_df['date'][::-1]]),
        y=pd.concat([p_df['yhat_upper'], p_df['yhat_lower'][::-1]]),
        fill='toself',
        fillcolor='rgba(247, 147, 26, 0.15)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Confidence Range'
    ))
    
    # Forecast line (orange)
    fig_pr.add_trace(go.Scatter(
        x=p_df['date'],
        y=p_df['yhat'],
        name='Forecast',
        line=dict(color='#F7931A', width=2.5)
    ))
    
    # Today line (dashed white)
    fig_pr.add_vline(x=p_df['date'].min(), line_width=1.5, line_dash="dash", line_color="#888888")
    
    fig_pr.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#333333", family="Inter, sans-serif"),
        xaxis=dict(gridcolor="#F0F0F0", showgrid=True),
        yaxis=dict(gridcolor="#F0F0F0", showgrid=True),
        legend=dict(bgcolor="white", bordercolor="#E8E8E8", borderwidth=1),
        height=300,
        margin=dict(l=40, r=20, t=20, b=40)
    )
    st.plotly_chart(fig_pr, use_container_width=True)

# Orange run fresh prediction button
if st.button("Run Fresh Prediction"):
    with st.spinner("Re-generating ensemble forecasts..."):
        res = safe_api_get("/api/predict/all")
        if res:
            st.toast("✅ Predictions updated successfully!", icon="🔮")
            st.rerun()
        else:
            st.toast("❌ Trigger failed. Backend offline.", icon="⚠️")

st.markdown("<br/>", unsafe_allow_html=True)

# Prediction history dataframe (styled)
st.markdown("### 📋 Prediction History Logs")
if history_data:
    h_df = pd.DataFrame(history_data)
    h_df["prediction_date"] = pd.to_datetime(h_df["prediction_date"]).dt.date
    h_df = h_df.sort_values("prediction_date", ascending=False)
    
    h_df["error_pct"] = (abs(h_df["predicted_value"] - h_df["actual_value"]) / h_df["actual_value"]) * 100
    
    df_disp = pd.DataFrame({
        "Date": h_df["prediction_date"],
        "Model": h_df["model_used"].str.upper(),
        "Predicted": h_df["predicted_value"].map(lambda x: f"${x:,.2f}" if pd.notnull(x) else "N/A"),
        "Actual": h_df["actual_value"].map(lambda x: f"${x:,.2f}" if pd.notnull(x) else "N/A"),
        "Error %": h_df["error_pct"].map(lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A")
    })
    
    def format_history_row(row):
        try:
            err = float(row["Error %"].replace("%", "").strip())
            if err <= 2.0:
                return ["color: #4CAF50; font-weight: bold;"] * len(row)
            elif err >= 5.0:
                return ["color: #F44336; font-weight: bold;"] * len(row)
        except Exception:
            pass
        return ["color: #555555;"] * len(row)
        
    st.dataframe(df_disp.style.apply(format_history_row, axis=1), use_container_width=True, hide_index=True)
else:
    st.info("No prediction history logs recorded.")
