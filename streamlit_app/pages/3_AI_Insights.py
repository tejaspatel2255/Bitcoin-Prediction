import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_app.utils import safe_api_get, format_date_str
from streamlit_app.components.sidebar import render_sidebar, start_live_clock

st.set_page_config(
    page_title="BTC Oracle | AI Insights",
    page_icon="🧠",
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

# ─── Load Latest Insights ───
with st.spinner("Retrieving latest AI report logs..."):
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
            "suggesting room for upward expansion. MACD is showing a minor bullish crossover, signaling weak "
            "buying pressure. High volatility persists, with Bollinger Bands slightly expanding."
        ),
        "prediction_explanation": (
            "Tomorrow's ensemble model predicts a target price of $69,210 (+1.11%). This projection is "
            "heavily weighted towards the Random Forest Regressor (60%), which is identifying bullish lag features "
            "in the 3-day close price indicators. The LSTM model (40%) is more conservative, forecasting $68,980 "
            "based on sequential lookback. Prophet forecasts a positive trend bias, resulting in a bullish ensemble direction."
        ),
        "risk_analysis": (
            "The risk posture for Bitcoin is currently assessed as MEDIUM. While short-term SMA trends are constructive, "
            "daily volatility remains elevated. An RSI value of 56 indicates that market conditions are neither "
            "overbought nor oversold. However, a break below the 21-day SMA at $66,900 would signal a bearish invalidation. "
            "Position sizes should remain moderate.\n\nRISK LEVEL: MEDIUM"
        ),
        "seven_day_outlook": (
            "Over the next week, the 7-day forecast indicates a gradual bullish ascent. Starting tomorrow, "
            "the price is expected to rise from $69,210 towards a weekend peak of $70,500. Some minor consolidation "
            "is expected by day 5, before ending the week near $71,200. The confidence range remains wide "
            "($66,500 – $73,000), suggesting volatility.\n\nSENTIMENT: BULLISH"
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

# Header
st.title("🧠 AI Intelligence Insights")
st.caption("Automated narrative analysis powered by OpenRouter AI (Google Gemini 1.5 Flash)")

# ─── Refresh Handlers ───
def trigger_refresh(endpoint_name: str, display_name: str):
    with st.spinner(f"Consulting AI for {display_name}..."):
        res = safe_api_get(f"/api/insights/{endpoint_name}")
        if res:
            st.toast(f"✅ Successfully refreshed {display_name}!", icon="💡")
            st.rerun()
        else:
            st.toast(f"❌ Failed to refresh {display_name}.", icon="⚠️")

# Generate Full Report Button
if st.button("🔄 Generate Full Insight Report", key="full_report_btn"):
    with st.spinner("Consulting AI and assembling full report..."):
        res = safe_api_get("/api/insights/full-report")
        if res:
            st.toast("✅ Full AI Insight Report regenerated successfully!", icon="🔥")
            st.rerun()
        else:
            st.toast("❌ Failed to regenerate full report.", icon="⚠️")

st.markdown("<hr style='border-color: rgba(255,255,255,0.05);'/>", unsafe_allow_html=True)

# ─── 4 Insight Cards with Custom Layout ───
col_l, col_r = st.columns(2)

with col_l:
    # Card 1: Market Summary
    st.markdown("### 🏪 Market Summary")
    st.markdown(f"""
    <div class="insight-box" style="border-left-color: #F7931A;">
        {latest_report.get('market_summary')}
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔄 Refresh Summary", key="ref_summary"):
        trigger_refresh("summary", "Market Summary")
        
    st.markdown("<br/>", unsafe_allow_html=True)
    
    # Card 2: Risk Analysis
    st.markdown("### ⚠️ Risk Analysis")
    st.markdown(f"""
    <div class="insight-box" style="border-left-color: #FF1744;">
        {latest_report.get('risk_analysis')}
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔄 Refresh Risk Analysis", key="ref_risk"):
        trigger_refresh("risk", "Risk Analysis")

with col_r:
    # Card 3: Prediction Explanation
    st.markdown("### 🤖 Prediction Explanation")
    st.markdown(f"""
    <div class="insight-box" style="border-left-color: #00E5FF;">
        {latest_report.get('prediction_explanation')}
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔄 Refresh Explanation", key="ref_explanation"):
        trigger_refresh("explanation", "Prediction Explanation")
        
    st.markdown("<br/>", unsafe_allow_html=True)
    
    # Card 4: 7-Day Outlook
    st.markdown("### 📅 7-Day Outlook")
    st.markdown(f"""
    <div class="insight-box" style="border-left-color: #00C853;">
        {latest_report.get('seven_day_outlook')}
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔄 Refresh Outlook", key="ref_outlook"):
        trigger_refresh("full-report", "7-Day Outlook")

# ─── Past Insights Expander at Bottom ───
st.markdown("---")
with st.expander("📋 Past AI Narrative HistoryLogs"):
    if history_data:
        raw_history_df = pd.DataFrame(history_data)
        hist_table = pd.DataFrame({
            "Created At": raw_history_df["created_at"].map(format_date_str),
            "Insight Section": raw_history_df["prompt_type"].map(lambda x: str(x).replace("_", " ").title()),
            "AI Narrative Text": raw_history_df["response_text"]
        })
        st.dataframe(hist_table, use_container_width=True, hide_index=True)
    else:
        st.info("No AI insights logs stored in database.")

# Update clock
start_live_clock(clock_placeholder)
