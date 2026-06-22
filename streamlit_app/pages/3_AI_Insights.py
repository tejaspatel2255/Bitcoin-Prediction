import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_app.utils import safe_api_get
from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.components.html_components import (
    render_topbar,
    insight_card,
    section_label
)

st.set_page_config(
    page_title="BTC Oracle | AI Insights",
    page_icon="🧠",
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

# ─── Load Latest Insights ───
with st.spinner("Loading latest AI intelligence..."):
    latest_report = safe_api_get("/api/insights/full-report")
    history_data = safe_api_get("/api/insights/history?limit=10")

# ─── Fallback/Simulation if API offline ───
if not latest_report:
    st.sidebar.warning("Running in simulation mode for AI Insights.")
    latest_report = {
        "market_summary": (
            "Bitcoin (BTC) is exhibiting consolidating price action, trading around the $68,450 support level. "
            "The 7-day Simple Moving Average (SMA) sits at $68,120, indicating a short-term bullish bias as "
            "price remains above this baseline. The Relative Strength Index (RSI) is in neutral territory at 56, "
            "suggesting room for upward expansion."
        ),
        "prediction_explanation": (
            "Tomorrow's ensemble model predicts a target price of $69,210 (+1.11%). This projection is "
            "heavily weighted towards the Random Forest Regressor (60%), which is identifying bullish lag features "
            "in the 3-day close price indicators. The LSTM model (40%) is forecasting $68,980."
        ),
        "risk_analysis": (
            "The risk posture for Bitcoin is currently assessed as MEDIUM. While short-term SMA trends are constructive, "
            "daily volatility remains elevated. An RSI value of 56 indicates that market conditions are neither "
            "overbought nor oversold. However, a break below the 21-day SMA at $66,900 would signal a bearish invalidation."
        ),
        "seven_day_outlook": (
            "Over the next week, the 7-day forecast indicates a gradual bullish ascent. Starting tomorrow, "
            "the price is expected to rise from $69,210 towards a weekend peak of $70,500."
        )
    }
    history_data = [
        {
            "id": 1,
            "created_at": datetime.now().isoformat(),
            "prompt_type": "market_summary",
            "response_text": latest_report["market_summary"]
        },
        {
            "id": 2,
            "created_at": datetime.now().isoformat(),
            "prompt_type": "prediction_explanation",
            "response_text": latest_report["prediction_explanation"]
        }
    ]

# Top Bar
render_topbar()

# Orange full width report generation button
if st.button("Generate Full Report"):
    with st.spinner("Generating consolidated market insights..."):
        res = safe_api_get("/api/insights/full-report")
        if res:
            st.toast("✅ Full report compiled successfully!", icon="🧠")
            st.rerun()
        else:
            st.toast("❌ Insight generator failed.", icon="⚠️")

# Section Label
section_label("🧠", "AI Insights")

# Helper to refresh segment
def trigger_segment_refresh(endpoint: str, label: str):
    with st.spinner(f"Refreshing {label}..."):
        res = safe_api_get(f"/api/insights/{endpoint}")
        if res:
            st.toast(f"✅ Refreshed {label} successfully!", icon="💡")
            st.rerun()
        else:
            st.toast(f"❌ Failed to refresh {label}.", icon="⚠️")

# 2x2 Grid Layout
col_g1, col_g2 = st.columns(2)

with col_g1:
    # Row 1 Left: Market Summary
    insight_card(
        icon="🏪",
        title="Market Summary",
        text=latest_report.get("market_summary"),
        border_color="#F7931A"
    )
    if st.button("🔄 Refresh Summary", key="ref_sum_btn"):
        trigger_segment_refresh("summary", "Market Summary")
        
    st.markdown("<br/>", unsafe_allow_html=True)
    
    # Row 2 Left: Risk Analysis
    insight_card(
        icon="⚠️",
        title="Risk Analysis",
        text=latest_report.get("risk_analysis"),
        border_color="#F44336"
    )
    if st.button("🔄 Refresh Risk", key="ref_risk_btn"):
        trigger_segment_refresh("risk", "Risk Analysis")

with col_g2:
    # Row 1 Right: Prediction Explanation
    insight_card(
        icon="🤖",
        title="Prediction Explanation",
        text=latest_report.get("prediction_explanation"),
        border_color="#60A5FA"
    )
    if st.button("🔄 Refresh Explanation", key="ref_exp_btn"):
        trigger_segment_refresh("explanation", "Prediction Explanation")
        
    st.markdown("<br/>", unsafe_allow_html=True)
    
    # Row 2 Right: 7-Day Outlook
    insight_card(
        icon="📅",
        title="7-Day Outlook",
        text=latest_report.get("seven_day_outlook"),
        border_color="#4CAF50"
    )
    if st.button("🔄 Refresh Outlook", key="ref_out_btn"):
        trigger_segment_refresh("full-report", "7-Day Outlook")

st.markdown("<hr style='border-color: rgba(255,255,255,0.05);'/>", unsafe_allow_html=True)
with st.expander("View history"):
    if history_data:
        h_df = pd.DataFrame(history_data)
        h_display = pd.DataFrame({
            "Timestamp": pd.to_datetime(h_df["created_at"]).dt.strftime("%Y-%m-%d %H:%M UTC"),
            "Section": h_df["prompt_type"].map(lambda x: str(x).replace("_", " ").title()),
            "AI Narrative Analysis": h_df["response_text"]
        })
        st.dataframe(h_display, use_container_width=True, hide_index=True)
    else:
        st.info("No saved insights logs.")
