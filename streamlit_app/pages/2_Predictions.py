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

st.set_page_config(
    page_title="BTC Oracle | Predictions",
    page_icon="🔮",
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

/* Custom prediction classes */
.pred-card {
    background: #1A1D27;
    border: 1px solid #F7931A22;
    border-radius: 12px;
    padding: 24px;
    text-align: center;
    min-height: 260px;
}
.direction-badge-bullish {
    background: #4CAF50;
    color: #FFFFFF;
    padding: 6px 16px;
    border-radius: 8px;
    font-weight: bold;
    display: inline-block;
    margin-bottom: 12px;
}
.direction-badge-bearish {
    background: #F44336;
    color: #FFFFFF;
    padding: 6px 16px;
    border-radius: 8px;
    font-weight: bold;
    display: inline-block;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

# Render Sidebar
render_sidebar()

# Title
st.title("🔮 Ensemble ML Predictions")

# "Run Fresh Prediction" button
if st.button("🔄 Run Fresh Prediction"):
    with st.spinner("Executing forecast & ML ensemble prediction pipeline..."):
        res = safe_api_get("/api/predict/all")
        if res:
            st.toast("✅ Ensemble model predictions generated successfully!", icon="🔮")
            st.rerun()
        else:
            st.toast("❌ Failed to trigger prediction. Check backend status.", icon="⚠️")

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

# Define standard Plotly Template
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

# ─── Top Row: 3 Columns ───
col_p1, col_p2, col_p3 = st.columns(3)

with col_p1:
    ens_p = next_day_data.get("ensemble_price", 0.0)
    low_b = ens_p * 0.985
    high_b = ens_p * 1.015
    st.markdown(f"""
    <div class="pred-card">
        <h4 style="margin: 0 0 10px; color: #888; font-weight: 500;">Next Day Forecast</h4>
        <h1 style="color: #F7931A; font-size: 2.5rem; margin: 15px 0;">${ens_p:,.2f}</h1>
        <p style="color: #888; font-size: 0.9rem; margin-top: 15px;">
            Estimated Range (95%):<br/>
            <strong style="color: #FFF;">${low_b:,.2f} - ${high_b:,.2f}</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

with col_p2:
    direction = direction_data.get("direction", "UP")
    confidence = direction_data.get("confidence", 50.0)
    
    badge_html = '<div class="direction-badge-bullish">BULLISH</div>' if direction == "UP" else '<div class="direction-badge-bearish">BEARISH</div>'
    gauge_color = "#4CAF50" if direction == "UP" else "#F44336"
    
    st.markdown(f"""
    <div class="pred-card" style="padding-bottom: 0;">
        <h4 style="margin: 0 0 15px; color: #888; font-weight: 500;">Directional Signal</h4>
        {badge_html}
    """, unsafe_allow_html=True)
    
    # Plotly gauge chart
    fig_g = go.Figure(go.Indicator(
        mode="gauge+number",
        value=confidence,
        number=dict(suffix="%", font=dict(color="#FFFFFF", size=20)),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor="#FFFFFF"),
            bar=dict(color=gauge_color),
            bgcolor="#1A1D27",
            bordercolor="rgba(247, 147, 26, 0.2)",
            steps=[
                {"range": [0, 50], "color": "#232733"},
                {"range": [50, 100], "color": "#2D3244"}
            ]
        )
    ))
    fig_g.update_layout(
        paper_bgcolor="#1A1D27",
        plot_bgcolor="#1A1D27",
        height=130,
        margin=dict(l=10, r=10, t=10, b=10)
    )
    st.plotly_chart(fig_g, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_p3:
    st.markdown("""
    <div class="pred-card" style="padding-bottom: 0;">
        <h4 style="margin: 0 0 15px; color: #888; font-weight: 500;">7-Day Forecast Trend</h4>
    """, unsafe_allow_html=True)
    
    # Sparkline from Prophet forecast
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
            paper_bgcolor="#1A1D27",
            plot_bgcolor="#1A1D27",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=140,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig_sp, use_container_width=True)
    else:
        st.write("No Prophet data for trend line.")
    st.markdown("</div>", unsafe_allow_html=True)

# ─── Ensemble Breakdown Chart ───
st.markdown("### 📊 Ensemble Model Price Forecasts")
lstm_p = next_day_data.get("lstm_price", 0.0)
rf_p = next_day_data.get("rf_price", 0.0)

fig_break = go.Figure()
fig_break.add_trace(go.Bar(
    y=["LSTM neural net", "Random Forest lags", "Ensemble consensus"],
    x=[lstm_p, rf_p, ens_p],
    orientation="h",
    marker_color="#F7931A",
    text=[f"${lstm_p:,.2f}", f"${rf_p:,.2f}", f"${ens_p:,.2f}"],
    textposition="auto"
))
fig_break.update_layout(
    template=template,
    xaxis=dict(gridcolor="#1E2130", showgrid=True, title="Predicted price ($)", range=[min(lstm_p, rf_p, ens_p)*0.98, max(lstm_p, rf_p, ens_p)*1.02]),
    yaxis=dict(gridcolor="#1E2130", showgrid=False),
    height=250,
    margin=dict(l=40, r=20, t=20, b=40)
)
st.plotly_chart(fig_break, use_container_width=True)

# ─── Prophet 7-Day Shaded Chart ───
st.markdown("### 📈 7-Day Shaded Projections (Prophet)")
if prophet_data and prophet_data.get("forecast"):
    p_df = pd.DataFrame(prophet_data["forecast"])
    p_df["date"] = pd.to_datetime(p_df["date"])
    
    fig_pr = go.Figure()
    
    # Shaded confidence band (opacity 0.15)
    fig_pr.add_trace(go.Scatter(
        x=pd.concat([p_df['date'], p_df['date'][::-1]]),
        y=pd.concat([p_df['yhat_upper'], p_df['yhat_lower'][::-1]]),
        fill='toself',
        fillcolor='rgba(247, 147, 26, 0.15)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Confidence Range'
    ))
    
    # Forecast line
    fig_pr.add_trace(go.Scatter(
        x=p_df['date'],
        y=p_df['yhat'],
        name='Forecast',
        line=dict(color='#F7931A', width=2.5)
    ))
    
    # Upper/Lower dashed lines
    fig_pr.add_trace(go.Scatter(x=p_df['date'], y=p_df['yhat_upper'], name='Upper Limit', line=dict(color='#F7931A', width=1, dash='dash')))
    fig_pr.add_trace(go.Scatter(x=p_df['date'], y=p_df['yhat_lower'], name='Lower Limit', line=dict(color='#F7931A', width=1, dash='dash')))
    
    # Today line
    fig_pr.add_vline(x=p_df['date'].min(), line_width=1.5, line_dash="dash", line_color="#FFFFFF")
    
    fig_pr.update_layout(
        template=template,
        height=300,
        margin=dict(l=40, r=20, t=20, b=40)
    )
    st.plotly_chart(fig_pr, use_container_width=True)

# ─── Prediction History Table with Conditional Styling ───
st.markdown("### 📋 Prediction History Logs")
if history_data:
    h_df = pd.DataFrame(history_data)
    h_df["prediction_date"] = pd.to_datetime(h_df["prediction_date"]).dt.date
    h_df = h_df.sort_values("prediction_date", ascending=False)
    
    # Calculate Error %
    h_df["error_pct"] = (abs(h_df["predicted_value"] - h_df["actual_value"]) / h_df["actual_value"]) * 100
    
    df_display = pd.DataFrame({
        "Date": h_df["prediction_date"],
        "Model": h_df["model_used"].str.upper(),
        "Predicted": h_df["predicted_value"].map(lambda x: f"${x:,.2f}" if pd.notnull(x) else "N/A"),
        "Actual": h_df["actual_value"].map(lambda x: f"${x:,.2f}" if pd.notnull(x) else "N/A"),
        "Error %": h_df["error_pct"].map(lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A")
    })
    
    # Function to apply conditional row formatting
    def style_rows(row):
        try:
            err_val = float(row["Error %"].replace("%", "").strip())
            if err_val <= 2.0:
                return ["color: #4CAF50; font-weight: bold;"] * len(row)
            elif err_val >= 5.0:
                return ["color: #F44336; font-weight: bold;"] * len(row)
        except Exception:
            pass
        return ["color: #E0E0E0;"] * len(row)
        
    styled_table = df_display.style.apply(style_rows, axis=1)
    st.dataframe(styled_table, use_container_width=True, hide_index=True)
else:
    st.info("No prediction history available yet.")
