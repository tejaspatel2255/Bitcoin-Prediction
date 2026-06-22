from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger("database")

db_url = settings.SUPABASE_DB_URL

# Create SQLAlchemy engine with connection pool parameters suitable for PostgreSQL
engine = None
SessionLocal = None

if db_url:
    try:
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        logger.info("Database engine and session factory created successfully.")
    except Exception as e:
        logger.error(f"Failed to create database engine: {e}")
else:
    logger.warning("SUPABASE_DB_URL is not set. Database functionality will be unavailable.")

Base = declarative_base()

def get_db():
    """
    Dependency helper function to yield a database session.
    Automatically closes the session after request completion.
    """
    if SessionLocal is None:
        logger.error("Database connection not configured. SessionLocal is None.")
        raise RuntimeError("Database connection not configured. Please check SUPABASE_DB_URL.")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
