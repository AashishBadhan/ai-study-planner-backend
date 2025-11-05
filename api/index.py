"""
Vercel Serverless Entry Point
Minimal FastAPI app for Vercel deployment
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create minimal app (no lifespan events for serverless)
app = FastAPI(
    title="AI Study Planner API",
    description="Backend API for AI-powered study planning",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "AI Study Planner API",
        "version": "1.0.0",
        "status": "running",
        "platform": "Vercel Serverless"
    }

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "platform": "vercel"
    }

@app.get("/api/test")
async def test():
    """Test endpoint"""
    return {"message": "API is working!"}

# Vercel handler
handler = app
