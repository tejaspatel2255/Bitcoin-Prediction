import pandas as pd
import datetime
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger("supabase_service")

def serialize_dates(obj: Any) -> Any:
    """
    Recursively convert date/datetime objects to ISO string representation to ensure JSON serializability.
    """
    if isinstance(obj, dict):
        return {k: serialize_dates(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_dates(x) for x in obj]
    elif isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    return obj

# Initialize the Supabase Client if URL and Key are provided
supabase: Optional[Client] = None

if settings.SUPABASE_URL and settings.SUPABASE_KEY:
    try:
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        logger.info("Supabase Client initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase Client: {e}")
else:
    logger.warning("Supabase URL and Key are missing in settings. Database operations will be mocked or throw errors.")

def insert_historical_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Upsert historical Bitcoin data from a pandas DataFrame into Supabase btc_historical_data table.
    """
    if not supabase:
        logger.error("Supabase client is not initialized.")
        return {"status": "error", "message": "Supabase client not initialized"}

    try:
        # Prepare DataFrame copy and convert dates to string format
        df_copy = df.copy()
        if 'date' in df_copy.columns:
            df_copy['date'] = df_copy['date'].astype(str)
        
        # Ensure all columns required exist in the records
        required_cols = ['date', 'open', 'high', 'low', 'close', 'volume', 'source']
        for col in required_cols:
            if col not in df_copy.columns:
                raise ValueError(f"Missing required column '{col}' in DataFrame")

        # Select only required columns for database
        df_records = df_copy[required_cols]
        records = df_records.to_dict(orient='records')
        
        logger.info(f"Upserting {len(records)} records into btc_historical_data table...")
        
        # Use upsert to handle potential duplicates on date key
        response = supabase.table("btc_historical_data").upsert(records).execute()
        
        logger.info("Successfully upserted historical data into Supabase.")
        return {"status": "success", "count": len(records), "data": response.data}
    except Exception as e:
        logger.error(f"Error in insert_historical_data: {e}")
        return {"status": "error", "message": str(e)}

def get_historical_data(days: int) -> pd.DataFrame:
    """
    Retrieve the last N days of historical Bitcoin data from Supabase btc_historical_data table.
    Returns a pandas DataFrame sorted by date in ascending order.
    """
    if not supabase:
        logger.error("Supabase client is not initialized.")
        return pd.DataFrame()

    try:
        logger.info(f"Fetching historical data for last {days} days from Supabase...")
        
        # Fetch descending by date and limit to retrieve the latest N records
        response = (
            supabase.table("btc_historical_data")
            .select("*")
            .order("date", desc=True)
            .limit(days)
            .execute()
        )
        
        data = response.data
        if not data:
            logger.warning("No historical data found in Supabase.")
            return pd.DataFrame()
            
        df = pd.DataFrame(data)
        
        # Sort ascending by date to return chronological ordering
        df = df.sort_values("date").reset_index(drop=True)
        df['date'] = pd.to_datetime(df['date']).dt.date
        
        return df
    except Exception as e:
        logger.error(f"Error in get_historical_data: {e}")
        return pd.DataFrame()

def insert_prediction(prediction_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Insert a machine learning forecast record into the predictions table.
    """
    if not supabase:
        logger.error("Supabase client is not initialized.")
        return {"status": "error", "message": "Supabase client not initialized"}

    try:
        # Convert date to string if passed as date object
        if 'prediction_date' in prediction_dict:
            prediction_dict['prediction_date'] = str(prediction_dict['prediction_date'])
            
        logger.info("Inserting prediction record into Supabase...")
        response = supabase.table("predictions").insert(prediction_dict).execute()
        
        logger.info("Prediction inserted successfully.")
        return {"status": "success", "data": response.data}
    except Exception as e:
        logger.error(f"Error in insert_prediction: {e}")
        return {"status": "error", "message": str(e)}

def get_predictions(limit: int) -> List[Dict[str, Any]]:
    """
    Retrieve predictions from Supabase table sorted by execution timestamp descending.
    """
    if not supabase:
        logger.error("Supabase client is not initialized.")
        return []

    try:
        logger.info(f"Fetching last {limit} predictions from Supabase...")
        response = (
            supabase.table("predictions")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data
    except Exception as e:
        logger.error(f"Error in get_predictions: {e}")
        return []

def insert_model_metrics(metrics_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Insert model evaluation metrics into the model_metrics table.
    """
    if not supabase:
        logger.error("Supabase client is not initialized.")
        return {"status": "error", "message": "Supabase client not initialized"}

    try:
        logger.info("Inserting model metrics record into Supabase...")
        response = supabase.table("model_metrics").insert(metrics_dict).execute()
        
        logger.info("Model metrics inserted successfully.")
        return {"status": "success", "data": response.data}
    except Exception as e:
        logger.error(f"Error in insert_model_metrics: {e}")
        return {"status": "error", "message": str(e)}

def insert_gemini_insight(insight_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Insert a Gemini generated insight record into the gemini_insights table.
    """
    if not supabase:
        logger.error("Supabase client is not initialized.")
        return {"status": "error", "message": "Supabase client not initialized"}

    try:
        serialized_insight = serialize_dates(insight_dict)
        logger.info("Inserting Gemini insight record into Supabase...")
        response = supabase.table("gemini_insights").insert(serialized_insight).execute()
        
        logger.info("Gemini insight inserted successfully.")
        return {"status": "success", "data": response.data}
    except Exception as e:
        logger.error(f"Error in insert_gemini_insight: {e}")
        return {"status": "error", "message": str(e)}

def get_latest_insights(limit: int) -> List[Dict[str, Any]]:
    """
    Retrieve the latest Gemini AI insights from Supabase sorted by creation date descending.
    """
    if not supabase:
        logger.error("Supabase client is not initialized.")
        return []

    try:
        logger.info(f"Fetching last {limit} Gemini insights from Supabase...")
        response = (
            supabase.table("gemini_insights")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data
    except Exception as e:
        logger.error(f"Error in get_latest_insights: {e}")
        return []

def get_model_metrics(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieve historical model training metrics from the model_metrics table.
    """
    if not supabase:
        logger.error("Supabase client is not initialized.")
        return []

    try:
        logger.info(f"Fetching last {limit} model metrics from Supabase...")
        response = (
            supabase.table("model_metrics")
            .select("*")
            .order("evaluated_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data
    except Exception as e:
        logger.error(f"Error in get_model_metrics: {e}")
        return []

def update_predictions_with_actuals() -> Dict[str, Any]:
    """
    Look for predictions with null actual_value, match them with close prices from btc_historical_data,
    and update the predictions table with actual close values and calculate error percentages.
    """
    if not supabase:
        logger.error("Supabase client is not initialized.")
        return {"status": "error", "message": "Supabase client not initialized"}

    try:
        # Fetch predictions where actual_value is null or not set
        response = (
            supabase.table("predictions")
            .select("id,prediction_date,predicted_value")
            .is_("actual_value", "null")
            .execute()
        )
        
        pending_preds = response.data or []
        if not pending_preds:
            logger.info("No pending predictions to update with actual values.")
            return {"status": "success", "updated_count": 0}
            
        # Get unique dates we need to look up
        dates = list(set([str(p["prediction_date"]) for p in pending_preds]))
        
        # Fetch actual close prices for these dates
        hist_resp = (
            supabase.table("btc_historical_data")
            .select("date,close")
            .in_("date", dates)
            .execute()
        )
        
        hist_data = hist_resp.data or []
        price_map = {str(h["date"]): float(h["close"]) for h in hist_data}
        
        updated_count = 0
        for p in pending_preds:
            date_str = str(p["prediction_date"])
            if date_str in price_map:
                actual = price_map[date_str]
                predicted = float(p["predicted_value"])
                error_pct = round((abs(predicted - actual) / actual) * 100, 2)
                
                # Update prediction row in database
                supabase.table("predictions").update({
                    "actual_value": actual,
                    "error_pct": error_pct
                }).eq("id", p["id"]).execute()
                updated_count += 1
                
        logger.info(f"Updated {updated_count} prediction records with actual price data.")
        return {"status": "success", "updated_count": updated_count}
    except Exception as e:
        logger.error(f"Error in update_predictions_with_actuals: {e}")
        return {"status": "error", "message": str(e)}


