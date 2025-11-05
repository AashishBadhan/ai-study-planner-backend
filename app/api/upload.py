"""
API Routes for File Upload and Processing
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import Optional
import os
import shutil
import logging
from pathlib import Path
from ..services.ocr_service import ocr_service
from ..services.nlp_service import nlp_service
from ..models.memory_db import Paper, QuestionDB
from ..models.schemas import PaperUploadResponse
from ..config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=PaperUploadResponse)
async def upload_paper(
    file: UploadFile = File(...),
    year: Optional[int] = Form(None),
    subject: Optional[str] = Form(None)
):
    """
    Upload and process an exam paper (PDF, Image, or Text)
    
    Steps:
    1. Validate and save file
    2. Extract text using OCR if needed
    3. Extract individual questions
    4. Classify questions by topics
    5. Store in database
    
    Returns:
        Processing results including extracted questions and topics
    """
    try:
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}"
            )
        
        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
            )
        
        # Save file
        file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File saved: {file_path}")
        
        # Determine file type
        file_type = "pdf" if file_ext == ".pdf" else \
                   "image" if file_ext in [".png", ".jpg", ".jpeg"] else "text"
        
        # Extract text
        logger.info("Extracting text from file...")
        extracted_text, errors = await ocr_service.extract_text(file_path, file_type)
        
        if not extracted_text:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to extract text from file. Errors: {errors}"
            )
        
        logger.info(f"Extracted {len(extracted_text)} characters")
        
        # Extract questions
        logger.info("Extracting questions...")
        questions = await nlp_service.extract_questions(extracted_text)
        
        if not questions:
            raise HTTPException(
                status_code=400,
                detail="No questions found in the document"
            )
        
        logger.info(f"Extracted {len(questions)} questions")
        
        # Classify questions into topics
        logger.info("Classifying questions by topics...")
        topics = await nlp_service.classify_questions(questions)
        
        # Calculate importance scores
        logger.info("Calculating importance scores...")
        importance_scores = await nlp_service.calculate_importance_scores(
            questions, topics, [year] * len(questions) if year else None
        )
        
        # Store in database
        paper_doc = await Paper.create(
            file_name=file.filename,
            file_type=file_type,
            extracted_text=extracted_text,
            questions=questions,
            topics=list(topics.keys())
        )
        
        # Store questions
        for question in questions:
            topic = None
            for topic_name, topic_questions in topics.items():
                if question in topic_questions:
                    topic = topic_name
                    break
            
            await QuestionDB.create(
                text=question,
                topic=topic or "General",
                year=year,
                importance_score=importance_scores.get(question, 0.0)
            )
        
        logger.info(f"Paper processed successfully. ID: {paper_doc['_id']}")
        
        return PaperUploadResponse(
            success=True,
            message="Paper uploaded and processed successfully",
            paper_id=paper_doc["_id"],
            extracted_text_length=len(extracted_text),
            questions_extracted=len(questions),
            topics_identified=list(topics.keys())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
    finally:
        # Clean up uploaded file (optional - you may want to keep it)
        # if os.path.exists(file_path):
        #     os.remove(file_path)
        pass


@router.get("/papers")
async def get_all_papers():
    """Get all uploaded papers"""
    try:
        papers = await Paper.get_all()
        return {"success": True, "papers": papers}
    except Exception as e:
        logger.error(f"Error fetching papers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/papers/{paper_id}")
async def get_paper(paper_id: str):
    """Get a specific paper by ID"""
    try:
        paper = await Paper.get_by_id(paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        return {"success": True, "paper": paper}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching paper: {e}")
        raise HTTPException(status_code=500, detail=str(e))
