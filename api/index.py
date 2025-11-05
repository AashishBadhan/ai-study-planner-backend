"""
Vercel Serverless Entry Point - Ultra Minimal
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
import os

# Create app
app = FastAPI()

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "AI Study Planner API is running on Vercel!", "status": "ok"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/api/test")
def test():
    return {"test": "success", "platform": "vercel"}

@app.post("/api/upload/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload endpoint for papers/images"""
    try:
        # Read file content
        content = await file.read()
        
        # For now, just return success (no actual storage in serverless)
        return {
            "success": True,
            "message": "File uploaded successfully",
            "filename": file.filename,
            "size": len(content),
            "type": file.content_type,
            "paper_id": "demo_paper_123",
            "note": "File processing is limited in serverless environment"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/upload/papers")
def get_papers():
    """Get uploaded papers"""
    return {
        "success": True,
        "papers": [],
        "message": "No papers stored (serverless mode)"
    }

@app.get("/api/analysis/topics")
def get_topics():
    """Get topics"""
    return {
        "success": True,
        "topics": ["Sample Topic 1", "Sample Topic 2"],
        "message": "Demo topics"
    }

@app.get("/api/analysis/questions")
def get_questions():
    """Get questions"""
    return {
        "success": True,
        "questions": [],
        "message": "No questions available"
    }

