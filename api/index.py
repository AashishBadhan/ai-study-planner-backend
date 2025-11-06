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
        
        # For now, just return success with expected response format
        return {
            "success": True,
            "message": "File uploaded successfully",
            "filename": file.filename,
            "paper_id": "demo_paper_123",
            "extracted_text_length": len(content),
            "questions_extracted": 5,  # Demo value
            "topics_identified": ["Sample Topic 1", "Sample Topic 2", "Sample Topic 3"],  # Demo topics
            "file_type": file.content_type,
            "note": "Demo mode - File processing limited in serverless"
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
def get_questions(topic: str = None, limit: int = 100):
    """Get questions"""
    # Return demo questions in expected format
    demo_questions = [
        {
            "_id": f"q{i}",
            "text": f"Sample question {i} about {topic or 'general topic'}?",
            "topic": topic or "General",
            "importance_score": 0.8 - (i * 0.05)
        }
        for i in range(1, 6)
    ]
    
    return {
        "success": True,
        "questions": demo_questions,
        "count": len(demo_questions),
        "message": "Demo questions (serverless mode)"
    }

