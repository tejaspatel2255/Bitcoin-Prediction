import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_app.utils import inject_premium_style, safe_api_get, safe_api_post, format_date_str

st.set_page_config(
    page_title="AI Insights | CryptoForecaster",
    page_icon="🤖",
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

# ─── Load Latest Insights ───
with st.spinner("Retrieving latest AI report logs..."):
    # Grab consolidated report data if available
    latest_report = safe_api_get("/api/insights/full-report")
    history_data = safe_api_get("/api/insights/history?limit=10")

# ─── Fallback/Simulation if API offline ───
if not latest_report:
    st.sidebar.warning("Running in simulation mode for AI Insights.")
    latest_report = {
        "market_summary": (
            "Bitcoin (BTC) is exhibiting consolidating price action, trading around the $64,250 support level. "
            "The 7-day Simple Moving Average (SMA) sits at $63,800, indicating a short-term bullish bias as "
            "price remains above this baseline. The Relative Strength Index (RSI) is in neutral territory at 54, "
            "suggesting room for upward expansion. MACD is showing a minor bullish crossover, signaling weak "
            "buying pressure. High volatility persists, with Bollinger Bands slightly expanding."
        ),
        "prediction_explanation": (
            "Tomorrow's ensemble model predicts a target price of $64,950 (+1.09%). This projection is "
            "heavily weighted towards the Random Forest Regressor (60%), which is identifying bullish lag features "
            "in the 3-day close price indicators. The LSTM model (40%) is more conservative, forecasting $64,700 "
            "based on sequential lookback. Prophet forecasts a positive trend bias, resulting in a bullish ensemble direction."
        ),
        "risk_analysis": (
            "The risk posture for Bitcoin is currently assessed as MEDIUM. While short-term SMA trends are constructive, "
            "daily volatility remains elevated. An RSI value of 54 indicates that market conditions are neither "
            "overbought nor oversold. However, a break below the 21-day SMA at $62,900 would signal a bearish invalidation. "
            "Position sizes should remain moderate.\n\nRISK LEVEL: MEDIUM"
        ),
        "seven_day_outlook": (
            "Over the next week, the 7-day forecast indicates a gradual bullish ascent. Starting tomorrow, "
            "the price is expected to rise from $64,950 towards a weekend peak of $66,200. Some minor consolidation "
            "is expected by day 5, before ending the week near $66,500. The confidence range remains wide "
            "($63,500 – $69,000), suggesting volatility.\n\nSENTIMENT: BULLISH"
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

# ─── Refresh Handlers ───
def refresh_insight(insight_type: str):
    """Call respective individual endpoints to refresh LLM insights."""
    endpoint_map = {
        "market_summary": "/api/insights/summary",
        "prediction_explanation": "/api/insights/explanation",
        "risk_analysis": "/api/insights/risk",
        "seven_day_outlook": "/api/insights/full-report"  # full-report generates all
    }
    endpoint = endpoint_map.get(insight_type)
    
    with st.spinner(f"Regenerating {insight_type.replace('_', ' ')} via OpenRouter..."):
        res = safe_api_get(endpoint)
        if res:
            st.success("Successfully generated fresh insight!")
            st.rerun()
        else:
            st.error("Failed to regenerate insight. Verify OpenRouter API key configuration.")

# ─── Main Content Layout ───
st.markdown("### 🤖 OpenRouter AI Market Intelligence Engine")
st.markdown("Automated natural language market narratives powered by google/gemini-flash-1.5.")

col1, col2 = st.columns(2)

with col1:
    # Card 1: Market Summary
    st.markdown("#### 📝 Current Market Summary")
    st.info(latest_report.get("market_summary"))
    if st.button("🔄 Refresh Summary", key="btn_summary"):
        refresh_insight("market_summary")
        
    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
    
    # Card 2: Risk Analysis
    st.markdown("#### ⚠️ Technical Risk Profile")
    st.info(latest_report.get("risk_analysis"))
    if st.button("🔄 Refresh Risk Analysis", key="btn_risk"):
        refresh_insight("risk_analysis")

with col2:
    # Card 3: Prediction Explanation
    st.markdown("#### 🧠 Model Forecast Explanation")
    st.info(latest_report.get("prediction_explanation"))
    if st.button("🔄 Refresh Explanation", key="btn_explanation"):
        refresh_insight("prediction_explanation")
        
    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
    
    # Card 4: 7-Day Outlook
    st.markdown("#### 📅 7-Day Market Sentiment")
    st.info(latest_report.get("seven_day_outlook"))
    if st.button("🔄 Refresh Outlook", key="btn_outlook"):
        refresh_insight("seven_day_outlook")

st.markdown("---")

# ─── History Section ───
st.markdown("### 📋 AI Insight Logs History")
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
