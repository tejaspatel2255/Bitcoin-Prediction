import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Supabase Configuration
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_DB_URL: str = ""

    # OpenRouter API Configuration (OpenAI-compatible, routes to Gemini Flash 1.5 free tier)
    OPENROUTER_API_KEY: str = ""
    GEMINI_MODEL: str = "google/gemini-2.5-flash"

    # FastAPI Settings
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    DEBUG: bool = True

    # Application Environment
    ENV: str = "development"

    # Configure Pydantic to read from environment variables or .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
