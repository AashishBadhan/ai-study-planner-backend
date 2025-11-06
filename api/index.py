"""
Vercel Serverless Entry Point - With MongoDB
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import db, Paper, QuestionDB
from app.config import settings

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

# Startup and shutdown events
@app.on_event("startup")
async def startup_db():
    """Connect to MongoDB on startup"""
    try:
        await db.connect_db()
        print("✅ MongoDB connected successfully")
    except Exception as e:
        print(f"⚠️  MongoDB connection failed: {e}")
        print("Continuing in demo mode...")

@app.on_event("shutdown")
async def shutdown_db():
    """Close MongoDB connection on shutdown"""
    await db.close_db()

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
        
        # Extract text (basic implementation)
        extracted_text = f"Extracted content from {file.filename}"
        
        # Demo questions and topics
        demo_questions = [
            {"text": f"Question 1 from {file.filename}?", "topic": "General", "importance_score": 0.9},
            {"text": f"Question 2 from {file.filename}?", "topic": "General", "importance_score": 0.8},
        ]
        demo_topics = ["General", "Study Material"]
        
        # Save to MongoDB
        try:
            paper = await Paper.create(
                file_name=file.filename,
                file_type=file.content_type,
                extracted_text=extracted_text,
                questions=demo_questions,
                topics=demo_topics
            )
            
            # Save questions to database
            for q in demo_questions:
                await QuestionDB.create(
                    text=q["text"],
                    topic=q["topic"],
                    importance_score=q["importance_score"]
                )
            
            return {
                "success": True,
                "message": "File uploaded and saved to MongoDB",
                "filename": file.filename,
                "paper_id": paper["_id"],
                "extracted_text_length": len(content),
                "questions_extracted": len(demo_questions),
                "topics_identified": demo_topics,
                "file_type": file.content_type,
            }
        except Exception as db_error:
            # Fallback to demo mode if MongoDB fails
            return {
                "success": True,
                "message": f"File uploaded (Demo mode - DB error: {str(db_error)})",
                "filename": file.filename,
                "paper_id": "demo_paper_123",
                "extracted_text_length": len(content),
                "questions_extracted": len(demo_questions),
                "topics_identified": demo_topics,
                "file_type": file.content_type,
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/upload/papers")
async def get_papers():
    """Get uploaded papers"""
    try:
        papers = await Paper.get_all()
        return {
            "success": True,
            "papers": papers,
            "count": len(papers)
        }
    except Exception as e:
        return {
            "success": True,
            "papers": [],
            "message": f"Demo mode - DB error: {str(e)}"
        }

@app.get("/api/analysis/topics")
@app.get("/api/analysis/questions")
async def get_questions(topic: str = None, limit: int = 100):
    """Get questions"""
    try:
        if topic:
            questions = await QuestionDB.get_by_topic(topic)
        else:
            questions = await QuestionDB.get_all()
        
        # Limit results
        questions = questions[:limit]
        
        return {
            "success": True,
            "questions": questions,
            "count": len(questions)
        }
    except Exception as e:
        # Fallback to demo data
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
            "message": f"Demo mode - DB error: {str(e)}"
        }   for i in range(1, 6)
    ]
    
    return {
        "success": True,
        "questions": demo_questions,
        "count": len(demo_questions),
        "message": "Demo questions (serverless mode)"
    }

