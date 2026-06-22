import streamlit as st
from datetime import datetime

def render_sidebar():
    st.sidebar.markdown("""
    <div style='text-align:center; padding: 20px 0 10px;'>
      <div style='background:#F7931A; width:52px; height:52px; border-radius:50%;
           display:inline-flex; align-items:center; justify-content:center;
           font-size:26px; font-weight:700; color:#fff; margin-bottom:10px;'>₿</div>
      <h1 style='color:#F7931A; font-size:22px; margin:0;'>BTC Oracle</h1>
      <p style='color:#888; font-size:11px; margin:4px 0 0;'>AI-Powered Prediction Engine</p>
    </div>
    <hr style='border-color:#F7931A22; margin:12px 0;'>
    """, unsafe_allow_html=True)
    
    st.sidebar.caption("Navigation")
    pages = {
        "🏠 Home": "Home.py", 
        "📊 Dashboard": "pages/1_Dashboard.py",
        "🔮 Predictions": "pages/2_Predictions.py",
        "🧠 AI Insights": "pages/3_AI_Insights.py",
        "📈 Model Performance": "pages/4_Model_Performance.py"
    }
    
    for name, path in pages.items():
        st.sidebar.page_link(path, label=name)
        
    st.sidebar.markdown("<hr style='border-color:#F7931A22;'>", unsafe_allow_html=True)
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    st.sidebar.caption(f"🕐 {now}")
    st.sidebar.markdown("<p style='color:#555;font-size:10px;text-align:center;margin-top:20px;'>Powered by OpenRouter AI<br>Prophet · LSTM · Random Forest</p>", unsafe_allow_html=True)
