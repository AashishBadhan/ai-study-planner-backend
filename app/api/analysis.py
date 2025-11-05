"""
API Routes for Analysis and Question Processing
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import logging
from ..services.nlp_service import nlp_service
from ..models.memory_db import QuestionDB, Paper
from ..models.schemas import AnalysisResponse, TopicAnalysis

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/analysis", response_model=AnalysisResponse)
async def get_analysis(
    topic: Optional[str] = Query(None, description="Filter by specific topic"),
    top_n: int = Query(20, description="Number of top questions to return")
):
    """
    Get comprehensive analysis of all questions
    
    Returns:
    - Total questions count
    - Topic distribution
    - Repeated questions
    - Important topics
    - Predicted important questions
    """
    try:
        # Fetch all questions
        if topic:
            questions = await QuestionDB.get_by_topic(topic)
        else:
            questions = await QuestionDB.get_all()
        
        if not questions:
            return AnalysisResponse(
                total_questions=0,
                topics=[],
                repeated_questions=[],
                important_topics=[],
                predictions=[],
                success=True
            )
        
        # Extract question texts and build mappings
        question_texts = [q['text'] for q in questions]
        importance_map = {q['text']: q.get('importance_score', 0.0) for q in questions}
        
        # Classify questions by topics
        logger.info("Classifying questions...")
        topics_dict = await nlp_service.classify_questions(question_texts)
        
        # Detect similar/repeated questions
        logger.info("Detecting similar questions...")
        similar_groups = await nlp_service.detect_similar_questions(question_texts)
        
        # Build topic analysis
        topic_analyses = []
        for topic_name, topic_questions in topics_dict.items():
            avg_importance = sum(importance_map.get(q, 0.0) for q in topic_questions) / len(topic_questions)
            
            topic_analyses.append(TopicAnalysis(
                topic=topic_name,
                frequency=len(topic_questions),
                importance_score=round(avg_importance, 3),
                questions=topic_questions[:5]  # Top 5 questions as preview
            ))
        
        # Sort topics by importance
        topic_analyses.sort(key=lambda x: x.importance_score, reverse=True)
        
        # Get important topics (top 5)
        important_topics = [t.topic for t in topic_analyses[:5]]
        
        # Get top predicted questions
        from ..services.study_planner import study_planner
        predictions = await study_planner.predict_important_questions(
            question_texts, importance_map, top_n
        )
        
        # Format predictions
        from ..models.schemas import Question
        prediction_objects = [
            Question(
                id=str(i),
                text=p['question'],
                importance_score=p['importance_score'],
                topic=None,  # Could enhance this
                frequency=1
            )
            for i, p in enumerate(predictions)
        ]
        
        return AnalysisResponse(
            total_questions=len(questions),
            topics=topic_analyses,
            repeated_questions=similar_groups[:10],  # Top 10 groups
            important_topics=important_topics,
            predictions=prediction_objects,
            success=True
        )
        
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/questions")
async def get_questions(
    topic: Optional[str] = Query(None),
    limit: int = Query(100, le=500)
):
    """Get questions with optional filtering"""
    try:
        if topic:
            questions = await QuestionDB.get_by_topic(topic)
        else:
            questions = await QuestionDB.get_all()
        
        # Limit results
        questions = questions[:limit]
        
        return {
            "success": True,
            "count": len(questions),
            "questions": questions
        }
    except Exception as e:
        logger.error(f"Error fetching questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/topics")
async def get_topics():
    """Get all unique topics"""
    try:
        questions = await QuestionDB.get_all()
        topics = set(q.get('topic', 'General') for q in questions)
        
        # Count questions per topic
        topic_counts = {}
        for q in questions:
            topic = q.get('topic', 'General')
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        return {
            "success": True,
            "topics": sorted(topics),
            "topic_counts": topic_counts
        }
    except Exception as e:
        logger.error(f"Error fetching topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similar-questions")
async def find_similar_questions(
    question: str = Query(..., description="Question text to find similar matches for"),
    threshold: float = Query(0.75, ge=0.0, le=1.0, description="Similarity threshold")
):
    """Find questions similar to the provided question"""
    try:
        # Get all questions
        all_questions = await QuestionDB.get_all()
        question_texts = [q['text'] for q in all_questions]
        
        # Add the query question
        combined = question_texts + [question]
        
        # Find similar
        similar = await nlp_service.detect_similar_questions(combined, threshold)
        
        # Filter for groups containing our query
        query_index = len(question_texts)
        relevant_groups = [
            g for g in similar if query_index in g['indices']
        ]
        
        return {
            "success": True,
            "query_question": question,
            "similar_groups": relevant_groups
        }
    except Exception as e:
        logger.error(f"Similar questions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
