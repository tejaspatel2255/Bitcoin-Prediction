import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logger import get_logger

# Import the new Phase 6 Routers
from app.api.routes.data import router as data_router
from app.api.routes.predictions import router as predictions_router
from app.api.routes.insights import router as insights_router
from app.api.routes.models import router as models_router

from app.services.data_service import start_data_scheduler, scheduled_ingestion_job
from app.models.model_manager import load_all_models

logger = get_logger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle FastAPI application lifecycle:
      - Startup: Load all ML models into memory and trigger fresh data ingestion.
      - Start the background APScheduler scheduler (every 6 hours).
      - Shutdown: Safely stop the background scheduler.
    """
    # ─── Startup Event ───
    logger.info("Starting up Bitcoin Prediction API Backend...")
    
    # 1. Load ML models from disk
    try:
        load_all_models()
        logger.info("Model Manager load completed at startup.")
    except Exception as e:
        logger.error(f"Error loading models at startup: {e}")

    # 2. Trigger fresh data ingestion synchronously to ensure DB has data
    try:
        logger.info("Executing initial Bitcoin data refresh...")
        scheduled_ingestion_job()
    except Exception as e:
        logger.error(f"Initial data refresh failed: {e}")
        
    # 3. Start the background APScheduler for 6-hourly updates
    scheduler = start_data_scheduler()

    yield  # Application runs here

    # ─── Shutdown Event ───
    logger.info("Shutting down Bitcoin Prediction API Backend...")
    try:
        scheduler.shutdown()
        logger.info("APScheduler stopped successfully.")
    except Exception as e:
        logger.error(f"Error stopping APScheduler: {e}")


# Initialize FastAPI application
app = FastAPI(
    title="Bitcoin Prediction Backend",
    description="Production-ready FastAPI backend featuring model manager pipelines and OpenRouter market insights.",
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan
)

# Enable CORS for Streamlit frontend or external client requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers with /api prefix
app.include_router(data_router, prefix="/api")
app.include_router(predictions_router, prefix="/api")
app.include_router(insights_router, prefix="/api")
app.include_router(models_router, prefix="/api")


@app.get("/")
def read_root():
    """Root redirect message."""
    return {
        "status": "online",
        "message": "Welcome to the Bitcoin Prediction API Backend",
        "docs_url": "/docs"
    }


@app.get("/health")
def health_check():
    """
    System Health Check endpoint. Returns state of database and loaded models.
    """
    from app.services.supabase_service import supabase
    db_status = "connected" if supabase is not None else "disconnected"
    
    try:
        status_dict = load_all_models()
    except Exception as e:
        status_dict = {"error": str(e)}

    return {
        "status": "healthy",
        "database_client": db_status,
        "models_loaded": status_dict
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
