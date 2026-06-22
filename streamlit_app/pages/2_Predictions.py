import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from streamlit_app.utils import inject_premium_style, safe_api_get

st.set_page_config(
    page_title="Predictions | CryptoForecaster",
    page_icon="🔮",
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

# ─── Load Predictions Data ───
with st.spinner("Generating predictions analysis..."):
    next_day_data = safe_api_get("/api/predict/next-day")
    direction_data = safe_api_get("/api/predict/direction")
    prophet_data = safe_api_get("/api/predict/7-day")
    history_data = safe_api_get("/api/predict/history?limit=30")

# ─── Fallback/Simulation if API offline ───
if not next_day_data:
    st.sidebar.warning("Running in simulation mode for Predictions.")
    # Simulate data
    latest_close = 64250.00
    ensemble_price = 64950.00
    lstm_price = 64700.00
    rf_price = 65100.00
    
    next_day_data = {
        "prediction_date": str((datetime.now() + timedelta(days=1)).date()),
        "ensemble_price": ensemble_price,
        "lstm_price": lstm_price,
        "rf_price": rf_price,
        "latest_close": latest_close,
        "percentage_change": 1.09
    }
    
    direction_data = {
        "prediction_date": next_day_data["prediction_date"],
        "direction": "UP",
        "confidence": 78.0
    }
    
    # Simulate Prophet forecast
    dates = [(datetime.now() + timedelta(days=i)).date() for i in range(1, 8)]
    forecast_list = []
    base_val = latest_close
    for i, d in enumerate(dates):
        base_val = base_val + (i * 150) + np.random.randn() * 300
        forecast_list.append({
            "date": str(d),
            "yhat": base_val,
            "yhat_lower": base_val - 1500 - (i * 200),
            "yhat_upper": base_val + 1500 + (i * 200)
        })
    prophet_data = {
        "prediction_date": next_day_data["prediction_date"],
        "forecast": forecast_list
    }
    
    # Simulate history data
    hist_dates = [(datetime.now() - timedelta(days=i)).date() for i in range(20, 0, -1)]
    history_list = []
    for i, d in enumerate(hist_dates):
        act_val = 60000 + (i * 200) + np.random.randn() * 500
        pred_val = act_val + np.random.randn() * 400
        history_list.append({
            "prediction_date": str(d),
            "model_used": "ensemble",
            "prediction_type": "price_forecast_1d",
            "predicted_value": pred_val,
            "actual_value": act_val,
            "confidence_score": 0.85 + (np.random.randn() * 0.05)
        })
    history_data = history_list

# ─── Main Content Layout ───
st.markdown("### 🔮 Next-Day Price Target & Signal")

col1, col2, col3 = st.columns([1, 1, 1.2])

with col1:
    ensemble_val = next_day_data.get("ensemble_price", 0.0)
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-title">Ensemble Price Target</div>
        <div class="metric-value">${ensemble_val:,.2f}</div>
        <div style="color: #94a3b8; font-size: 0.85rem;">Target Date: {next_day_data.get('prediction_date')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Model breakdown in small card
    st.markdown(f"""
    <div style="background: rgba(30, 41, 59, 0.25); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 15px;">
        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: #cbd5e1; margin-bottom: 5px;">
            <span>LSTM Price Model (40%):</span>
            <strong>${next_day_data.get('lstm_price', 0.0):,.2f}</strong>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: #cbd5e1;">
            <span>Random Forest Lag (60%):</span>
            <strong>${next_day_data.get('rf_price', 0.0):,.2f}</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    direction = direction_data.get("direction", "NEUTRAL")
    dir_class = "metric-delta-positive" if direction == "UP" else "metric-delta-negative"
    sign = "▲" if direction == "UP" else "▼"
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-title">Forecast Direction</div>
        <div class="metric-value {dir_class}">{direction} {sign}</div>
        <div style="color: #94a3b8; font-size: 0.85rem;">Implication on daily returns</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    confidence = direction_data.get("confidence", 50.0)
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-title">Model Confidence Score</div>
        <div class="metric-value">{confidence:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Probability Bar
    st.progress(confidence / 100.0)

st.markdown("---")

# ─── Charts: Prophet 7-Day & Actual vs Predicted ───
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("### 📈 Prophet 7-Day Outlook Chart")
    if prophet_data and prophet_data.get("forecast"):
        p_df = pd.DataFrame(prophet_data["forecast"])
        p_df["date"] = pd.to_datetime(p_df["date"])
        
        fig = go.Figure()
        
        # Shaded Confidence Interval bounds
        fig.add_trace(go.Scatter(
            x=pd.concat([p_df['date'], p_df['date'][::-1]]),
            y=pd.concat([p_df['yhat_upper'], p_df['yhat_lower'][::-1]]),
            fill='toself',
            fillcolor='rgba(99, 102, 241, 0.15)',
            line=dict(color='rgba(255,255,255,0)'),
            name='Confidence Interval',
            showlegend=True
        ))
        
        # Predicted Trend Line
        fig.add_trace(go.Scatter(
            x=p_df['date'],
            y=p_df['yhat'],
            name='Prophet Projections (yhat)',
            line=dict(color='#818cf8', width=2.5)
        ))
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(gridcolor='rgba(255,255,255,0.05)', color='#94a3b8'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.05)', color='#94a3b8', title="USD ($)"),
            legend=dict(font=dict(color='#cbd5e1'), bgcolor='rgba(15, 23, 42, 0.6)'),
            height=380
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Prophet forecasting is currently processing.")

with chart_col2:
    st.markdown("### 🎯 Actual vs Predicted Prices")
    if history_data:
        h_df = pd.DataFrame(history_data)
        # Filter only ensemble predictions for single-line consistency
        h_df = h_df[h_df["model_used"] == "ensemble"].copy()
        
        if not h_df.empty:
            h_df["prediction_date"] = pd.to_datetime(h_df["prediction_date"])
            h_df = h_df.sort_values("prediction_date")
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=h_df["prediction_date"],
                y=h_df["actual_value"],
                name="Actual Spot Close",
                line=dict(color="#10b981", width=2.5)
            ))
            fig.add_trace(go.Scatter(
                x=h_df["prediction_date"],
                y=h_df["predicted_value"],
                name="Ensemble Forecast Target",
                line=dict(color="#f59e0b", width=2, dash="dash")
            ))
            
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis=dict(gridcolor='rgba(255,255,255,0.05)', color='#94a3b8'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.05)', color='#94a3b8', title="USD ($)"),
                legend=dict(font=dict(color='#cbd5e1'), bgcolor='rgba(15, 23, 42, 0.6)'),
                height=380
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No ensemble forecast history matches found.")
    else:
        st.info("No prediction database logs found.")

st.markdown("---")

# ─── Predictions Log History Table ───
st.markdown("### 📋 Prediction History Logs")
if history_data:
    raw_table_df = pd.DataFrame(history_data)
    # Format table for cleaner rendering
    table_df = pd.DataFrame({
        "Target Date": raw_table_df["prediction_date"],
        "Model Type": raw_table_df["model_used"],
        "Forecast Type": raw_table_df["prediction_type"],
        "Predicted Target": raw_table_df["predicted_value"].map(lambda x: f"${x:,.2f}" if pd.notnull(x) else "N/A"),
        "Actual Price": raw_table_df["actual_value"].map(lambda x: f"${x:,.2f}" if pd.notnull(x) else "N/A"),
        "Confidence Index": raw_table_df["confidence_score"].map(lambda x: f"{x * 100:.1f}%" if pd.notnull(x) else "N/A")
    })
    st.dataframe(table_df, use_container_width=True, hide_index=True)
else:
    st.info("No prediction database records available.")
