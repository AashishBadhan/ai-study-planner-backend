"""
API Routes for Study Schedule Generation
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
import logging
from datetime import datetime
from ..services.study_planner import study_planner
from ..services.nlp_service import nlp_service
from ..models.memory_db import QuestionDB, Schedule
from ..models.schemas import StudyScheduleRequest, StudyScheduleResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate", response_model=StudyScheduleResponse)
async def generate_schedule(request: StudyScheduleRequest):
    """
    Generate a personalized study schedule
    
    Input:
    - available_hours: Total study time available
    - study_duration: Study session length (minutes)
    - break_duration: Break length (minutes)
    - start_date: Optional start date
    - exam_date: Optional exam date
    - topics_to_include: Optional list of topics to focus on
    
    Output:
    - Complete study schedule with sessions
    - Topic time distribution
    - Total sessions and hours
    """
    try:
        # Fetch questions
        questions = await QuestionDB.get_all()
        
        if not questions:
            raise HTTPException(
                status_code=400,
                detail="No questions available. Please upload exam papers first."
            )
        
        # Extract data
        question_texts = [q['text'] for q in questions]
        importance_map = {q['text']: q.get('importance_score', 0.0) for q in questions}
        
        # Classify into topics
        logger.info("Classifying questions for schedule generation...")
        topics = await nlp_service.classify_questions(question_texts)
        
        # Filter topics if specified
        if request.topics_to_include:
            topics = {
                k: v for k, v in topics.items() 
                if k in request.topics_to_include
            }
        
        if not topics:
            raise HTTPException(
                status_code=400,
                detail="No topics found matching criteria"
            )
        
        # Generate schedule
        logger.info(f"Generating schedule for {request.available_hours} hours...")
        schedule = await study_planner.generate_schedule(
            topics=topics,
            importance_scores=importance_map,
            available_hours=request.available_hours,
            study_duration=request.study_duration,
            break_duration=request.break_duration,
            start_date=request.start_date,
            exam_date=request.exam_date
        )
        
        # Save schedule to database
        user_id = "default_user"  # In production, get from auth
        await Schedule.create(user_id, schedule.dict())
        
        logger.info(f"Schedule generated: {schedule.total_sessions} sessions")
        
        return schedule
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Schedule generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate schedule: {str(e)}")


@router.get("/schedules")
async def get_schedules(user_id: str = "default_user"):
    """Get all schedules for a user"""
    try:
        schedules = await Schedule.get_by_user(user_id)
        return {
            "success": True,
            "count": len(schedules),
            "schedules": schedules
        }
    except Exception as e:
        logger.error(f"Error fetching schedules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict-questions")
async def predict_questions(top_n: int = 20):
    """
    Predict most important questions for upcoming exam
    Based on frequency, recency, and topic importance
    """
    try:
        questions = await QuestionDB.get_all()
        
        if not questions:
            raise HTTPException(
                status_code=400,
                detail="No questions available"
            )
        
        question_texts = [q['text'] for q in questions]
        importance_map = {q['text']: q.get('importance_score', 0.0) for q in questions}
        
        predictions = await study_planner.predict_important_questions(
            question_texts, importance_map, top_n
        )
        
        return {
            "success": True,
            "count": len(predictions),
            "predictions": predictions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
