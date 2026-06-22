import os
import sys

# Adjust Python path to resolve backend modules from root directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.supabase_service import supabase
from app.core.logger import get_logger

logger = get_logger("setup_db_health")

def verify_table(table_name: str) -> bool:
    """
    Perform a test query on a table to verify its existence.
    """
    if not supabase:
        return False
        
    try:
        # Dry-run limit 1 select query to check schema existence
        supabase.table(table_name).select("*").limit(1).execute()
        return True
    except Exception as e:
        err_msg = str(e)
        if "does not exist" in err_msg or "404" in err_msg:
            logger.error(f"❌ Table '{table_name}' does not exist in the database.")
        else:
            logger.error(f"⚠️ Error verifying '{table_name}': {err_msg}")
        return False

def run_health_check():
    logger.info("=" * 65)
    logger.info("SUPABASE DATABASE HEALTH CHECK & TABLE VERIFICATION REPORT")
    logger.info("=" * 65)

    if not supabase:
        logger.error("❌ Critical: Supabase client could not be initialized.")
        logger.error("Please verify that SUPABASE_URL and SUPABASE_KEY are set in your .env file.")
        sys.exit(1)

    tables_to_check = [
        "btc_historical_data",
        "predictions",
        "model_metrics",
        "gemini_insights"
    ]

    all_passed = True
    report = []

    for table in tables_to_check:
        logger.info(f"Verifying table: {table}...")
        exists = verify_table(table)
        if exists:
            report.append((table, "✅ ONLINE (Active)"))
        else:
            report.append((table, "❌ OFFLINE (Missing or Error)"))
            all_passed = False

    print("\n" + "=" * 50)
    print("           DATABASE HEALTH SUMMARY")
    print("=" * 50)
    for table, status in report:
        print(f" {table:<25} : {status}")
    print("=" * 50)

    if all_passed:
        print("🎉 SUCCESS: All database tables are present and healthy!")
        logger.info("Database setup verification complete: SUCCESS.")
    else:
        print("⚠️ WARNING: Some tables are missing or returned errors.")
        print("Please check scripts/setup_db.sql and execute it in the Supabase SQL editor.")
        logger.warning("Database setup verification complete: WARNING (missing tables).")
        sys.exit(1)

if __name__ == "__main__":
    run_health_check()
