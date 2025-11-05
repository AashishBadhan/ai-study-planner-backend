"""
Main FastAPI Application
AI Study Planner Backend Server
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from datetime import datetime

from .config import settings
from .models.memory_db import memory_db as db
from .services.nlp_service import nlp_service
from .api import upload, analysis, schedule, timer

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting AI Study Planner application...")
    
    try:
        # Connect to database (optional for Vercel)
        try:
            await db.connect_db()
            logger.info("Database connected")
        except Exception as db_error:
            logger.warning(f"Database connection failed (will work in limited mode): {db_error}")
        
        # Initialize NLP model (optional - will use fallback if not available)
        try:
            await nlp_service.initialize()
            logger.info("NLP model loaded")
        except Exception as nlp_error:
            logger.warning(f"NLP model loading failed (using fallback): {nlp_error}")
        
        logger.info("Application startup complete")
        
    except Exception as e:
        logger.error(f"Startup warning: {e}")
        # Don't raise - allow app to start even with errors
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    try:
        await db.close_db()
    except:
        pass
    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="AI Study Planner API",
    description="Backend API for AI-powered study planning and exam preparation",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "name": "AI Study Planner API",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db_status = "connected" if db.db is not None else "disconnected"
        
        # Check NLP model
        model_loaded = nlp_service.model is not None
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_status,
            "ml_model_loaded": model_loaded
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


# Include routers
app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(schedule.router, prefix="/api/schedule", tags=["Schedule"])
app.include_router(timer.router, prefix="/api/timer", tags=["Timer"])


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle uncaught exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
