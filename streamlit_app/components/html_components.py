import streamlit as st

def render_topbar(last_updated="2 min ago"):
    st.markdown(f"""
    <div style="display:flex; align-items:center; justify-content:space-between;
         background:#1A1D27; padding:14px 20px; border-radius:12px;
         border:1px solid #2A2D3A; margin-bottom:20px;">
      <div style="display:flex; align-items:center; gap:12px;">
        <div style="width:42px;height:42px;border-radius:50%;background:#F7931A;
             display:flex;align-items:center;justify-content:center;
             font-size:22px;font-weight:700;color:#fff;">₿</div>
        <div>
          <div style="font-size:18px;font-weight:700;color:#FFFFFF;">BTC Oracle</div>
          <div style="font-size:11px;color:#888;">AI-Powered Prediction Engine</div>
        </div>
      </div>
      <div style="display:flex; align-items:center; gap:14px;">
        <span style="font-size:12px;color:#888;">Last updated: {last_updated}</span>
        <span style="background:#1a3a1a;border:1px solid #2d6a2d;color:#4CAF50;
              font-size:11px;padding:5px 12px;border-radius:20px;font-weight:600;">
          ● Live
        </span>
      </div>
    </div>
    """, unsafe_allow_html=True)

def metric_card(icon, label, value, delta, delta_color="#4CAF50"):
    st.markdown(f"""
    <div style="background:#FFFFFF;border:1px solid #E8E8E8;border-radius:12px;
         padding:16px;box-shadow:0 1px 4px rgba(0,0,0,0.06);">
      <div style="font-size:11px;color:#888;text-transform:uppercase;
           letter-spacing:0.5px;margin-bottom:6px;">{icon} {label}</div>
      <div style="font-size:22px;font-weight:700;color:#1A1A1A;">{value}</div>
      <div style="font-size:12px;color:{delta_color};margin-top:4px;font-weight:500;">
        {delta}
      </div>
    </div>
    """, unsafe_allow_html=True)

def section_label(icon, label):
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;margin:20px 0 12px;">
      <span style="font-size:13px;color:#888;font-weight:600;">
        {icon} {label.upper()}
      </span>
      <div style="flex:1;height:1px;background:#2A2D3A;"></div>
    </div>
    """, unsafe_allow_html=True)

def prediction_card(predicted, low, high, direction, confidence):
    dir_color = "#4CAF50" if direction == "Bullish" else "#F44336"
    dir_bg = "rgba(76,175,80,0.12)" if direction == "Bullish" else "rgba(244,67,54,0.12)"
    arrow = "↗" if direction == "Bullish" else "↘"
    bar_color = "#4CAF50" if direction == "Bullish" else "#F44336"
    st.markdown(f"""
    <div style="background:#FFFFFF;border:1px solid #E8E8E8;border-radius:12px;padding:18px;">
      <div style="font-size:11px;color:#888;text-transform:uppercase;
           letter-spacing:0.5px;margin-bottom:10px;">🔮 Next Day Prediction</div>
      <div style="font-size:28px;font-weight:700;color:#F7931A;">${predicted:,.0f}</div>
      <div style="font-size:12px;color:#999;margin:4px 0 12px;">
        Range: ${low:,.0f} — ${high:,.0f}
      </div>
      <span style="background:{dir_bg};color:{dir_color};border:1px solid {dir_color}33;
            padding:6px 14px;border-radius:20px;font-size:13px;font-weight:600;">
        {arrow} {direction}
      </span>
      <div style="margin-top:14px;">
        <div style="display:flex;justify-content:space-between;
             font-size:12px;color:#888;margin-bottom:5px;">
          <span>Confidence</span><span>{confidence}%</span>
        </div>
        <div style="background:#F0F0F0;border-radius:4px;height:7px;">
          <div style="background:{bar_color};width:{confidence}%;
               height:7px;border-radius:4px;"></div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

def insight_card(icon, title, text, border_color, timestamp=""):
    st.markdown(f"""
    <div style="background:#FFFFFF;border:1px solid #E8E8E8;border-radius:12px;
         padding:16px;border-left:4px solid {border_color};
         box-shadow:0 1px 3px rgba(0,0,0,0.05);height:100%;">
      <div style="font-size:13px;font-weight:600;color:#1A1A1A;
           margin-bottom:8px;">{icon} {title}</div>
      <div style="font-size:12px;color:#555;line-height:1.7;">{text}</div>
      <div style="margin-top:12px;">
        <span style="font-size:10px;background:#FFF3E0;color:#F7931A;
              border:1px solid #FFE0B2;padding:3px 10px;border-radius:20px;">
          via OpenRouter · Gemini Flash
        </span>
      </div>
      {'<div style="font-size:10px;color:#BBB;margin-top:6px;">'+timestamp+'</div>' if timestamp else ''}
    </div>
    """, unsafe_allow_html=True)

def model_card(icon, name, subtitle, accuracy, acc_color="#4CAF50"):
    st.markdown(f"""
    <div style="background:#FFFFFF;border:1px solid #E8E8E8;border-radius:12px;
         padding:14px 16px;display:flex;align-items:center;gap:12px;
         box-shadow:0 1px 3px rgba(0,0,0,0.05);">
      <div style="width:36px;height:36px;border-radius:8px;background:#FFF3E0;
           display:flex;align-items:center;justify-content:center;font-size:18px;">
        {icon}
      </div>
      <div style="flex:1;">
        <div style="font-size:13px;font-weight:600;color:#1A1A1A;">{name}</div>
        <div style="font-size:11px;color:#888;">{subtitle}</div>
      </div>
      <div style="font-size:18px;font-weight:700;color:{acc_color};">{accuracy}%</div>
    </div>
    """, unsafe_allow_html=True)
