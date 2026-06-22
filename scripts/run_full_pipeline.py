import os
import sys
from datetime import datetime, timedelta

# Ensure parent directory is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.logger import get_logger
from app.services import data_service, prediction_service, gemini_service, supabase_service
from app.models import model_manager
from scripts.seed_data import main as run_seed
from scripts.train import main as run_train

logger = get_logger("full_pipeline")

def main():
    logger.info("=" * 65)
    logger.info("       🚀 RUNNING COMPLETE BITCOIN ANALYTICS PIPELINE 🚀")
    logger.info("=" * 65)

    # ─── 1. Run Data Seeding ───
    logger.info("\n[1/4] Running Data Ingestion & Seeding Pipeline...")
    try:
        run_seed()
        logger.info("✅ Data seeding successful.")
    except Exception as e:
        logger.error(f"❌ Data seeding failed: {e}")
        sys.exit(1)

    # ─── 2. Model Training ───
    logger.info("\n[2/4] Training Forecasting Models (Prophet, LSTM, RF)...")
    try:
        run_train()
        logger.info("✅ Model training pipeline completed.")
    except Exception as e:
        logger.error(f"❌ Model training failed: {e}")
        sys.exit(1)

    # ─── 3. Run Predictions & Forecasts ───
    logger.info("\n[3/4] Running Inference Pipeline & Generating Targets...")
    preds = {}
    try:
        preds = prediction_service.generate_predictions()
        logger.info(f"✅ Prediction inference complete. Saved {preds.get('saved_count', 0)} predictions.")
    except Exception as e:
        logger.error(f"❌ Prediction generation failed: {e}")
        sys.exit(1)

    # ─── 4. Generate AI Insights via OpenRouter ───
    logger.info("\n[4/4] Generating OpenRouter AI Market Insights (Gemini 1.5)...")
    insights = {}
    try:
        df_hist = data_service.add_technical_indicators(supabase_service.get_historical_data(days=90))
        
        # Format prediction fields as expected by insight engine
        preds_for_insights = {
            "prediction_date": preds.get("prediction_date"),
            "prophet_price": preds.get("prophet_price"),
            "lstm_price": preds.get("lstm_price"),
            "rf_price": preds.get("rf_price"),
            "ensemble_price": preds.get("ensemble_price"),
            "rf_direction": preds.get("rf_direction"),
            "latest_close": float(df_hist.iloc[-1]["close"]) if not df_hist.empty else 0.0,
            "prophet_7day": preds.get("prophet_7day")  # Can be empty or None, fallback handles it
        }
        
        insights = gemini_service.generate_full_report(df_hist, preds_for_insights)
        logger.info("✅ AI Insights report successfully generated & stored in Supabase.")
    except Exception as e:
        logger.error(f"❌ AI Insights generation failed: {e}")

    # ─── 5. Complete Status Report ───
    print("\n" + "=" * 65)
    print("           ✨ BITCOIN AI PIPELINE EXECUTION STATUS ✨")
    print("=" * 65)
    print(f" Timestamp      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Data Ingestion : SUCCESS")
    print(f" Model Training : SUCCESS")
    print(f" Predictions    : SUCCESS")
    print(f"   - Target Date: {preds.get('prediction_date')}")
    print(f"   - Ensemble   : ${preds.get('ensemble_price', 0.0):,.2f}")
    print(f"   - Direction  : {preds.get('rf_direction', 'N/A')}")
    print(f" AI Insights    : {'SUCCESS' if insights else 'FAILED/SKIPPED'}")
    print("=" * 65)
    print("Pipeline Execution Complete.\n")

if __name__ == "__main__":
    main()
