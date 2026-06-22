import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_app.utils import safe_api_get
from streamlit_app.components.sidebar import render_sidebar

st.set_page_config(
    page_title="BTC Oracle | AI Insights",
    page_icon="🧠",
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

/* Custom insight box helper classes */
.insight-card {
    background: #1A1D27;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 12px;
    color: #E0E0E0;
    line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)

# Render Sidebar
render_sidebar()

# Title
st.title("🧠 AI Intelligence Insights")

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

# Generate Full Report Button (Orange, full width)
if st.button("🔄 Generate Full Report", key="full_report_gen"):
    with st.spinner("Consulting AI & generating full consolidated report..."):
        res = safe_api_get("/api/insights/full-report")
        if res:
            st.toast("✅ Full AI Market Intelligence report generated!", icon="🧠")
            st.rerun()
        else:
            st.toast("❌ Failed to generate report. Check API credentials.", icon="⚠️")

st.markdown("<br/>", unsafe_allow_html=True)

# ─── Refresh Handlers ───
def trigger_refresh_section(endpoint_name: str, display_name: str):
    with st.spinner(f"Refreshing {display_name}..."):
        res = safe_api_get(f"/api/insights/{endpoint_name}")
        if res:
            st.toast(f"✅ Refreshed {display_name} successfully!", icon="💡")
            st.rerun()
        else:
            st.toast(f"❌ Failed to refresh {display_name}.", icon="⚠️")

# ─── 2x2 Grid of Insight Cards ───
col_grid_l, col_grid_r = st.columns(2)

with col_grid_l:
    # Card 1: Market Summary
    st.markdown(f"""
    <div class="insight-card" style="border-left: 4px solid #F7931A;">
        <h4 style="margin: 0 0 10px; color: #F7931A;">🏪 Market Summary</h4>
        <p style="margin: 0; font-size: 0.95rem; line-height: 1.6;">{latest_report.get("market_summary")}</p>
        <span style="display: block; font-size: 0.75rem; color: #888; margin-top: 15px;">Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}</span>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔄 Refresh Summary", key="ref_sum"):
        trigger_refresh_section("summary", "Market Summary")
        
    st.markdown("<br/>", unsafe_allow_html=True)

    # Card 2: Risk Analysis
    st.markdown(f"""
    <div class="insight-card" style="border-left: 4px solid #F44336;">
        <h4 style="margin: 0 0 10px; color: #F44336;">⚠️ Risk Analysis</h4>
        <p style="margin: 0; font-size: 0.95rem; line-height: 1.6;">{latest_report.get("risk_analysis")}</p>
        <span style="display: block; font-size: 0.75rem; color: #888; margin-top: 15px;">Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}</span>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔄 Refresh Risk Analysis", key="ref_risk"):
        trigger_refresh_section("risk", "Risk Analysis")

with col_grid_r:
    # Card 3: Prediction Explanation
    st.markdown(f"""
    <div class="insight-card" style="border-left: 4px solid #60A5FA;">
        <h4 style="margin: 0 0 10px; color: #60A5FA;">🤖 Prediction Explanation</h4>
        <p style="margin: 0; font-size: 0.95rem; line-height: 1.6;">{latest_report.get("prediction_explanation")}</p>
        <span style="display: block; font-size: 0.75rem; color: #888; margin-top: 15px;">Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}</span>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔄 Refresh Explanation", key="ref_exp"):
        trigger_refresh_section("explanation", "Prediction Explanation")
        
    st.markdown("<br/>", unsafe_allow_html=True)

    # Card 4: 7-Day Outlook
    st.markdown(f"""
    <div class="insight-card" style="border-left: 4px solid #4CAF50;">
        <h4 style="margin: 0 0 10px; color: #4CAF50;">📅 7-Day Outlook</h4>
        <p style="margin: 0; font-size: 0.95rem; line-height: 1.6;">{latest_report.get("seven_day_outlook")}</p>
        <span style="display: block; font-size: 0.75rem; color: #888; margin-top: 15px;">Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}</span>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔄 Refresh Outlook", key="ref_out"):
        trigger_refresh_section("full-report", "7-Day Outlook")

# ─── Past Insights Expander at Bottom ───
st.markdown("---")
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
        st.info("No saved insights in the logs.")
