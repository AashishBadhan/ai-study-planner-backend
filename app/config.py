"""
Configuration module for AI Study Planner backend
Handles environment variables and application settings
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Database Configuration
    DATABASE_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "ai_study_planner"
    
    # Security
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    # Upload Configuration
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    UPLOAD_DIR: str = "./uploads"
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".png", ".jpg", ".jpeg", ".txt"]
    
    # ML Model Configuration
    MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    DEVICE: str = "cpu"  # or "cuda" for GPU
    
    # Study Timer Defaults (in minutes)
    DEFAULT_STUDY_DURATION: int = 25
    DEFAULT_BREAK_DURATION: int = 5
    DEFAULT_LONG_BREAK_DURATION: int = 15
    POMODOROS_UNTIL_LONG_BREAK: int = 4
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        # Allow extra fields from environment
        extra = "ignore"


# Global settings instance
settings = Settings()

# Ensure upload directory exists (skip on serverless)
try:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
except:
    pass  # Serverless environments may not allow directory creation
