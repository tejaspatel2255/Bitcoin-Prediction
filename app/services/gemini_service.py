import google.generativeai as genai
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger("gemini_service")

def generate_market_insight(prediction_data: dict, latest_price_data: dict) -> dict:
    """
    Generate conversational market analysis and sentiment using Google Gemini 1.5 Flash.
    """
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        logger.warning("GEMINI_API_KEY not configured. Returning fallback AI insight.")
        return {
            "insight_text": "AI Insights are currently unavailable because the Google Gemini API Key is not set in the configuration. Please check your environment variables.",
            "sentiment_score": "NEUTRAL"
        }

    try:
        # Configure Gemini SDK
        genai.configure(api_key=api_key)
        
        # Instantiate Gemini 1.5 Flash model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Build prompt using prediction and technical data
        prompt = f"""
You are an expert financial analyst and cryptocurrency researcher.
Analyze the following technical indicators and machine learning models' predictions for Bitcoin (BTC) and provide a concise, professional market report (approx 200-300 words).

Latest Market Data:
- Date: {latest_price_data.get('date')}
- Close Price: ${latest_price_data.get('close_price'):,.2f}
- Open Price: ${latest_price_data.get('open_price'):,.2f}
- High: ${latest_price_data.get('high_price'):,.2f} / Low: ${latest_price_data.get('low_price'):,.2f}
- Volume: {latest_price_data.get('volume'):,.0f}
- RSI (14): {latest_price_data.get('rsi_14') if latest_price_data.get('rsi_14') else 'N/A'}
- MACD Line: {latest_price_data.get('macd') if latest_price_data.get('macd') else 'N/A'}
- MACD Signal Line: {latest_price_data.get('macd_signal') if latest_price_data.get('macd_signal') else 'N/A'}

ML Models Predictions (for tomorrow {prediction_data.get('prediction_date')}):
- Prophet Predicted Close: ${prediction_data.get('prophet_price'):,.2f}
- LSTM Predicted Close: ${prediction_data.get('lstm_price'):,.2f}
- Scikit-learn (Random Forest) Predicted Close: ${prediction_data.get('sklearn_price'):,.2f}
- Ensemble Predicted Close (Weighted Avg): ${prediction_data.get('ensemble_price'):,.2f}
- Predicted Direction: {prediction_data.get('predicted_direction')} (compared to today's close)
- 7-Day Trend: {prediction_data.get('trend_7day')}

Instructions:
1. Explain what the combination of technical indicators (RSI, MACD) and predictions suggests (e.g. if the market is overbought, oversold, or trending).
2. Synthesize the findings into a clear, actionable observation for traders. Do not provide direct financial advice, rather highlight key risk factors and opportunities.
3. At the very end of your response, specify the overall market sentiment on a new line exactly as 'SENTIMENT: BULLISH', 'SENTIMENT: BEARISH', or 'SENTIMENT: NEUTRAL'. Do not add any punctuation to this line.
"""
        logger.info("Requesting market insight from Gemini 1.5 Flash...")
        
        # Call Gemini model
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=500
            )
        )
        
        insight_text = response.text.strip()
        
        # Parse sentiment from the final lines
        sentiment_score = "NEUTRAL"
        lines = insight_text.split('\n')
        for line in reversed(lines):
            if "SENTIMENT:" in line.upper():
                sentiment_part = line.split(":")[-1].strip().upper()
                if sentiment_part in ["BULLISH", "BEARISH", "NEUTRAL"]:
                    sentiment_score = sentiment_part
                    # Remove the sentiment line from the main insight text to keep UI clean
                    insight_text = "\n".join([l for l in lines if l != line]).strip()
                    break

        logger.info(f"Successfully generated Gemini insight. Sentiment: {sentiment_score}")
        return {
            "insight_text": insight_text,
            "sentiment_score": sentiment_score
        }

    except Exception as e:
        logger.error(f"Error communicating with Gemini: {e}")
        return {
            "insight_text": f"Error generating AI Insight: {e}",
            "sentiment_score": "NEUTRAL"
        }
