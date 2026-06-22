"""
app/services/gemini_service.py — AI Insight Engine using OpenRouter API.

OpenRouter is OpenAI-compatible and provides access to Google Gemini Flash 1.5
on a generous free tier via the standard OpenAI Python SDK.

Base URL:  https://openrouter.ai/api/v1
Model:     google/gemini-flash-1.5
SDK:       openai (pip install openai>=1.0.0)
"""

import time
import pandas as pd
from openai import OpenAI, RateLimitError, APIError
from app.core.config import settings
from app.core.logger import get_logger
from app.core.prompts import (
    MARKET_SUMMARY_PROMPT,
    PREDICTION_EXPLANATION_PROMPT,
    RISK_ANALYSIS_PROMPT,
    SEVEN_DAY_OUTLOOK_PROMPT
)
from app.services.supabase_service import insert_gemini_insight

logger = get_logger("gemini_service")

# ─── OpenRouter Configuration ─────────────────────────────────────────────────
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL    = "google/gemini-flash-1.5"
MAX_RETRIES         = 3
_client: OpenAI | None = None


def init_openrouter() -> OpenAI:
    """
    Initialize and return an OpenAI client pointed at the OpenRouter API.
    Uses a module-level singleton to avoid re-instantiating on every call.

    Returns:
        Configured OpenAI client instance.
    """
    global _client
    if _client is not None:
        return _client

    api_key = settings.OPENROUTER_API_KEY
    if not api_key:
        logger.warning("OPENROUTER_API_KEY is not set. AI insight calls will be skipped.")
        return None

    _client = OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=api_key,
        default_headers={
            "HTTP-Referer": "http://localhost:8501",  # Identifies the app to OpenRouter
            "X-Title":      "BTC Prediction App"
        }
    )
    logger.info(f"OpenRouter client initialized. Model: {OPENROUTER_MODEL}")
    return _client


def _call_openrouter(prompt: str, prompt_type: str, context_data: dict) -> str:
    """
    Internal helper: send a prompt to OpenRouter and return the response text.
    Implements exponential backoff retry on rate limit / API errors.
    Persists prompt + response to Supabase gemini_insights table.

    Args:
        prompt:       Fully formatted prompt string to send.
        prompt_type:  Short identifier for the prompt category (for DB storage).
        context_data: Raw context dict used to build the prompt (stored as JSON).

    Returns:
        Response text from the model, or a fallback error string on failure.
    """
    client = init_openrouter()
    if client is None:
        return "AI Insights unavailable: OPENROUTER_API_KEY is not configured."

    response_text = None
    last_error    = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Calling OpenRouter [{prompt_type}] — Attempt {attempt}/{MAX_RETRIES}...")
            completion = client.chat.completions.create(
                model=OPENROUTER_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional cryptocurrency market analyst. "
                            "Provide concise, data-driven analysis. "
                            "Never provide direct financial advice."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=600
            )
            response_text = completion.choices[0].message.content.strip()
            logger.info(f"OpenRouter [{prompt_type}] succeeded on attempt {attempt}.")
            break

        except RateLimitError as e:
            wait = 2 ** attempt  # Exponential backoff: 2s, 4s, 8s
            logger.warning(f"Rate limit hit [{prompt_type}] attempt {attempt}. Retrying in {wait}s...")
            last_error = e
            time.sleep(wait)

        except APIError as e:
            wait = 2 ** attempt
            logger.error(f"API error [{prompt_type}] attempt {attempt}: {e}. Retrying in {wait}s...")
            last_error = e
            time.sleep(wait)

        except Exception as e:
            logger.error(f"Unexpected error calling OpenRouter [{prompt_type}]: {e}")
            last_error = e
            break

    if response_text is None:
        response_text = f"AI Insight generation failed after {MAX_RETRIES} attempts: {last_error}"
        logger.error(response_text)
    else:
        # Persist to Supabase gemini_insights table
        try:
            insert_gemini_insight({
                "prompt_type":   prompt_type,
                "response_text": response_text,
                "context_json":  context_data
            })
        except Exception as db_err:
            logger.warning(f"Failed to persist AI insight to Supabase: {db_err}")

    return response_text


# ─── 1. Market Summary ─────────────────────────────────────────────────────────
def generate_market_summary(latest_data: dict) -> str:
    """
    Summarize current BTC market conditions from OHLCV + technical indicators.

    Args:
        latest_data: Dict with OHLCV + indicator fields from add_technical_indicators().

    Returns:
        Market summary as a formatted string.
    """
    prompt = MARKET_SUMMARY_PROMPT.format(
        date        = latest_data.get("date",         "N/A"),
        open        = float(latest_data.get("open",        0)),
        high        = float(latest_data.get("high",        0)),
        low         = float(latest_data.get("low",         0)),
        close       = float(latest_data.get("close",       0)),
        volume      = float(latest_data.get("volume",      0)),
        sma_7       = float(latest_data.get("sma_7",       0)),
        sma_21      = float(latest_data.get("sma_21",      0)),
        ema_12      = float(latest_data.get("ema_12",      0)),
        ema_26      = float(latest_data.get("ema_26",      0)),
        rsi_14      = float(latest_data.get("rsi_14",      50)),
        macd        = float(latest_data.get("macd",        0)),
        macd_signal = float(latest_data.get("macd_signal", 0)),
        bb_upper    = float(latest_data.get("bb_upper",    0)),
        bb_lower    = float(latest_data.get("bb_lower",    0)),
        daily_return = float(latest_data.get("daily_return", 0)),
        volatility  = float(latest_data.get("volatility", 0))
    )
    return _call_openrouter(prompt, "market_summary", latest_data)


# ─── 2. Prediction Explanation ─────────────────────────────────────────────────
def generate_prediction_explanation(predictions: dict) -> str:
    """
    Explain in plain language what the ML models predict and why.

    Args:
        predictions: Dict returned by prediction_service.generate_predictions().

    Returns:
        Explanation as a formatted string.
    """
    latest_close  = float(predictions.get("latest_close",  0) or 0)
    ensemble_price = float(predictions.get("ensemble_price", latest_close) or latest_close)
    pct_change    = ((ensemble_price - latest_close) / latest_close * 100) if latest_close else 0

    prompt = PREDICTION_EXPLANATION_PROMPT.format(
        prediction_date = predictions.get("prediction_date", "N/A"),
        prophet_price   = float(predictions.get("prophet_price",  0) or 0),
        lstm_price      = float(predictions.get("lstm_price",     0) or 0),
        rf_price        = float(predictions.get("rf_price",       0) or 0),
        ensemble_price  = ensemble_price,
        rf_direction    = predictions.get("rf_direction", "N/A"),
        latest_close    = latest_close,
        pct_change      = pct_change
    )
    return _call_openrouter(prompt, "prediction_explanation", predictions)


# ─── 3. Risk Analysis ──────────────────────────────────────────────────────────
def generate_risk_analysis(predictions: dict, indicators: dict) -> str:
    """
    Assess Bitcoin position risk level based on volatility, RSI, MACD, and predictions.

    Args:
        predictions: Dict from prediction_service.generate_predictions().
        indicators:  Dict of latest technical indicators (from add_technical_indicators).

    Returns:
        Risk analysis as a formatted string.
    """
    latest_close   = float(predictions.get("latest_close", 0) or 0)
    ensemble_price = float(predictions.get("ensemble_price", latest_close) or latest_close)
    pct_change     = ((ensemble_price - latest_close) / latest_close * 100) if latest_close else 0

    prompt = RISK_ANALYSIS_PROMPT.format(
        rsi_14        = float(indicators.get("rsi_14",       50)),
        macd          = float(indicators.get("macd",          0)),
        macd_signal   = float(indicators.get("macd_signal",   0)),
        volatility    = float(indicators.get("volatility",    0)),
        daily_return  = float(indicators.get("daily_return",  0)),
        bb_upper      = float(indicators.get("bb_upper",      0)),
        bb_lower      = float(indicators.get("bb_lower",      0)),
        close         = float(indicators.get("close",         0)),
        ensemble_price = ensemble_price,
        rf_direction  = predictions.get("rf_direction", "N/A"),
        pct_change    = pct_change
    )
    return _call_openrouter(prompt, "risk_analysis", {**predictions, **indicators})


# ─── 4. 7-Day Outlook ──────────────────────────────────────────────────────────
def generate_7day_outlook(prophet_forecast: dict, current_price: float) -> str:
    """
    Generate a narrative 7-day Bitcoin outlook from the Prophet forecast DataFrame.

    Args:
        prophet_forecast: Dict with key 'prophet_7day' → pd.DataFrame
                          (columns: date, yhat, yhat_lower, yhat_upper).
        current_price:    Today's close price as float.

    Returns:
        7-day outlook narrative as a formatted string.
    """
    forecast_df = prophet_forecast.get("prophet_7day", pd.DataFrame())
    if forecast_df.empty:
        return "7-Day Outlook unavailable: Prophet forecast data is missing."

    # Build forecast table string for the prompt
    rows = []
    for _, row in forecast_df.iterrows():
        rows.append(
            f"  {row['date']}: ${row['yhat']:,.2f} "
            f"(range: ${row['yhat_lower']:,.2f} – ${row['yhat_upper']:,.2f})"
        )
    forecast_table = "\n".join(rows)

    last_row  = forecast_df.iloc[-1]
    end_price = float(last_row["yhat"])
    lower     = float(last_row["yhat_lower"])
    upper     = float(last_row["yhat_upper"])
    projected_pct = ((end_price - current_price) / current_price * 100) if current_price else 0
    start_date    = forecast_df.iloc[0]["date"]

    prompt = SEVEN_DAY_OUTLOOK_PROMPT.format(
        start_date     = start_date,
        forecast_table = forecast_table,
        current_price  = current_price,
        projected_pct  = projected_pct,
        end_price      = end_price,
        lower          = lower,
        upper          = upper
    )
    context = {
        "current_price": current_price,
        "end_price": end_price,
        "projected_pct": projected_pct
    }
    return _call_openrouter(prompt, "7day_outlook", context)


# ─── Combined Full Report ──────────────────────────────────────────────────────
def generate_full_report(df: "pd.DataFrame", predictions: dict) -> dict:
    """
    Run all 4 insight generators and return a combined report dict.

    Args:
        df:          DataFrame with technical indicators (from add_technical_indicators).
        predictions: Dict from prediction_service.generate_predictions().

    Returns:
        Dict with keys:
          - market_summary         : str
          - prediction_explanation : str
          - risk_analysis          : str
          - seven_day_outlook      : str
    """
    # Extract latest row as dict for indicator-based prompts
    df_sorted   = df.sort_values("date").reset_index(drop=True)
    latest_dict = df_sorted.iloc[-1].to_dict()
    # Convert date to string for JSON serialization
    if "date" in latest_dict:
        latest_dict["date"] = str(latest_dict["date"])

    current_price = float(latest_dict.get("close", 0))

    logger.info("Generating full AI insight report (4 sections)...")

    report = {
        "market_summary":         generate_market_summary(latest_dict),
        "prediction_explanation": generate_prediction_explanation(predictions),
        "risk_analysis":          generate_risk_analysis(predictions, latest_dict),
        "seven_day_outlook":      generate_7day_outlook(predictions, current_price)
    }

    logger.info("Full AI insight report generated successfully.")
    return report
