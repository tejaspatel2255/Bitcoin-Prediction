import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logger import get_logger
from app.core.database import engine, Base
from app.api.historical import router as historical_router
from app.api.predictions import router as predictions_router
from app.api.insights import router as insights_router
from app.api.dashboard import router as dashboard_router

logger = get_logger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown using modern lifespan pattern."""
    # --- Startup ---
    logger.info("Starting up Bitcoin Prediction API backend...")
    if engine:
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Successfully checked/created database tables.")
        except Exception as e:
            logger.error(f"Failed to initialize database tables: {e}")
    else:
        logger.warning("Database engine is not initialized. Skipping database startup checks.")

    yield  # Application runs here

    # --- Shutdown ---
    logger.info("Shutting down Bitcoin Prediction API backend...")

# Initialize FastAPI App with lifespan
app = FastAPI(
    title="Bitcoin Prediction API",
    description="Backend API for historical market data, predictions (Prophet, LSTM, Random Forest), and Gemini AI market insights.",
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(historical_router, prefix="/api")
app.include_router(predictions_router, prefix="/api")
app.include_router(insights_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Welcome to the Bitcoin Prediction API",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
