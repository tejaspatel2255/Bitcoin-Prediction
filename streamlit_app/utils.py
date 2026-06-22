import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# API base url configuration
API_BASE_URL = "http://127.0.0.1:8000"

def get_api_url(endpoint: str) -> str:
    """Helper to construct full endpoint URL."""
    return f"{API_BASE_URL}/{endpoint.lstrip('/')}"


def inject_premium_style():
    """Injects global, premium dark glassmorphism styles and fonts into Streamlit."""
    st.markdown("""
    <style>
        /* Outfit and Plus Jakarta Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', sans-serif;
            color: #f8fafc;
        }
        
        /* Headers styling */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Outfit', sans-serif;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: -0.5px;
        }
        
        /* Premium Card style */
        .glass-card {
            background: rgba(30, 41, 59, 0.45);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .glass-card:hover {
            border-color: rgba(245, 158, 11, 0.4);
            box-shadow: 0 12px 40px rgba(245, 158, 11, 0.1);
            transform: translateY(-2px);
        }
        
        /* Metric Styling */
        .metric-title {
            color: #94a3b8;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }
        
        .metric-value {
            color: #ffffff;
            font-size: 2.2rem;
            font-weight: 700;
            line-height: 1;
            margin-bottom: 8px;
        }
        
        .metric-delta-positive {
            color: #10b981;
            font-weight: 600;
            font-size: 0.95rem;
            display: flex;
            align-items: center;
        }
        
        .metric-delta-negative {
            color: #ef4444;
            font-weight: 600;
            font-size: 0.95rem;
            display: flex;
            align-items: center;
        }
        
        /* Premium Banner Container */
        .header-banner {
            background: linear-gradient(135deg, #1e1b4b 0%, #311042 50%, #0f172a 100%);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 18px;
            padding: 35px;
            margin-bottom: 30px;
            box-shadow: 0 12px 35px rgba(0, 0, 0, 0.5);
        }
        
        .premium-badge {
            background: linear-gradient(90deg, #f59e0b 0%, #d97706 100%);
            color: #ffffff;
            padding: 4px 14px;
            border-radius: 50px;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.5px;
            display: inline-block;
            text-transform: uppercase;
            margin-bottom: 12px;
        }
    </style>
    """, unsafe_allow_html=True)

def safe_api_get(endpoint: str, cache: bool = True) -> dict:
    """
    Safely execute a GET request to the FastAPI backend.
    Returns response data or logs warnings.
    """
    url = get_api_url(endpoint)
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            logger_warning(f"Endpoint {endpoint} returned status code {response.status_code}")
    except Exception as e:
        logger_warning(f"Connection to backend failed at {url}: {e}")
    return {}

def safe_api_post(endpoint: str, payload: dict = None) -> dict:
    """Safely execute a POST request to the FastAPI backend."""
    url = get_api_url(endpoint)
    try:
        response = requests.post(url, json=payload or {}, timeout=30)
        return response.json()
    except Exception as e:
        logger_warning(f"POST request to {url} failed: {e}")
    return {"status": "error", "message": "Failed to contact backend api."}

def logger_warning(msg: str):
    """Print standard dashboard warnings."""
    st.sidebar.warning(msg)

def format_date_str(val) -> str:
    """Format dates beautifully."""
    if not val:
        return "N/A"
    try:
        dt = datetime.fromisoformat(str(val).replace("Z", ""))
        return dt.strftime("%B %d, %Y at %H:%M")
    except:
        return str(val)
