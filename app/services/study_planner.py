"""
Study Planner Service
Generates personalized study schedules based on topic importance and available time
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ..models.schemas import StudySession, StudyScheduleResponse
from ..config import settings

logger = logging.getLogger(__name__)


class StudyPlannerService:
    """Service for generating study schedules"""
    
    async def generate_schedule(
        self,
        topics: Dict[str, List[str]],
        importance_scores: Dict[str, float],
        available_hours: float,
        study_duration: int = 25,
        break_duration: int = 5,
        start_date: Optional[datetime] = None,
        exam_date: Optional[datetime] = None
    ) -> StudyScheduleResponse:
        """
        Generate a personalized study schedule
        
        Args:
            topics: Dictionary of topic names to question lists
            importance_scores: Question importance scores
            available_hours: Total available study hours
            study_duration: Study session duration in minutes
            break_duration: Break duration in minutes
            start_date: Schedule start date
            exam_date: Exam date
            
        Returns:
            Complete study schedule
        """
        try:
            # Calculate topic importance and allocate time
            topic_importance = self._calculate_topic_importance(topics, importance_scores)
            topic_hours = self._allocate_time_to_topics(topic_importance, available_hours)
            
            # Generate study sessions
            sessions = self._create_study_sessions(
                topics, 
                topic_hours, 
                importance_scores,
                study_duration,
                break_duration
            )
            
            # Calculate total sessions
            total_sessions = len(sessions)
            total_study_time = sum(session.duration_minutes for session in sessions) / 60
            
            # Format dates
            start_str = start_date.isoformat() if start_date else None
            exam_str = exam_date.isoformat() if exam_date else None
            
            logger.info(f"Generated schedule with {total_sessions} sessions across {len(topic_hours)} topics")
            
            return StudyScheduleResponse(
                total_hours=round(total_study_time, 2),
                total_sessions=total_sessions,
                sessions=sessions,
                topic_distribution=topic_hours,
                start_date=start_str,
                exam_date=exam_str
            )
            
        except Exception as e:
            logger.error(f"Schedule generation error: {e}")
            raise
    
    def _calculate_topic_importance(
        self, 
        topics: Dict[str, List[str]], 
        importance_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate overall importance score for each topic
        Based on average importance of questions in that topic
        """
        topic_importance = {}
        
        for topic_name, questions in topics.items():
            if not questions:
                topic_importance[topic_name] = 0.0
                continue
            
            # Calculate average importance of questions in this topic
            topic_scores = [importance_scores.get(q, 0.5) for q in questions]
            avg_score = sum(topic_scores) / len(topic_scores)
            
            # Weight by number of questions (more questions = more important)
            question_weight = min(1.0, len(questions) / 10)  # Cap at 10 questions
            
            # Combined importance
            combined = (0.7 * avg_score) + (0.3 * question_weight)
            topic_importance[topic_name] = round(combined, 3)
        
        return topic_importance
    
    def _allocate_time_to_topics(
        self, 
        topic_importance: Dict[str, float], 
        total_hours: float
    ) -> Dict[str, float]:
        """
        Allocate study time to topics proportionally to their importance
        
        Args:
            topic_importance: Topic importance scores
            total_hours: Total available study hours
            
        Returns:
            Dictionary mapping topic to allocated hours
        """
        if not topic_importance:
            return {}
        
        # Calculate total importance
        total_importance = sum(topic_importance.values())
        
        if total_importance == 0:
            # Equal distribution if all topics have 0 importance
            hours_per_topic = total_hours / len(topic_importance)
            return {topic: round(hours_per_topic, 2) for topic in topic_importance}
        
        # Proportional allocation
        topic_hours = {}
        for topic, importance in topic_importance.items():
            allocated = (importance / total_importance) * total_hours
            topic_hours[topic] = round(allocated, 2)
        
        # Ensure minimum time for each topic (at least 30 minutes)
        min_hours = 0.5
        for topic in topic_hours:
            if topic_hours[topic] < min_hours and total_hours >= min_hours * len(topic_hours):
                topic_hours[topic] = min_hours
        
        # Normalize to match total hours
        current_total = sum(topic_hours.values())
        if current_total > 0:
            scale_factor = total_hours / current_total
            topic_hours = {t: round(h * scale_factor, 2) for t, h in topic_hours.items()}
        
        return topic_hours
    
    def _create_study_sessions(
        self,
        topics: Dict[str, List[str]],
        topic_hours: Dict[str, float],
        importance_scores: Dict[str, float],
        study_duration: int,
        break_duration: int
    ) -> List[StudySession]:
        """
        Create individual study sessions from topic allocations
        
        Args:
            topics: Topic to questions mapping
            topic_hours: Allocated hours per topic
            importance_scores: Question importance scores
            study_duration: Session duration in minutes
            break_duration: Break duration in minutes
            
        Returns:
            List of study sessions
        """
        sessions = []
        session_number = 0
        current_day = 1
        daily_study_time = 0  # minutes
        max_daily_time = 4 * 60  # 4 hours max per day
        
        # Sort topics by allocated time (descending)
        sorted_topics = sorted(topic_hours.items(), key=lambda x: x[1], reverse=True)
        
        for topic_name, allocated_hours in sorted_topics:
            if topic_name not in topics:
                continue
            
            # Convert hours to minutes
            total_minutes = allocated_hours * 60
            questions = topics[topic_name]
            
            # Calculate number of sessions needed for this topic
            num_sessions = max(1, int(total_minutes / study_duration))
            minutes_per_session = total_minutes / num_sessions
            
            # Get top questions by importance
            topic_questions = sorted(
                questions,
                key=lambda q: importance_scores.get(q, 0.0),
                reverse=True
            )
            
            # Distribute questions across sessions
            questions_per_session = max(1, len(topic_questions) // num_sessions)
            
            for i in range(num_sessions):
                # Check if we need to move to next day
                if daily_study_time + minutes_per_session > max_daily_time:
                    current_day += 1
                    daily_study_time = 0
                
                # Get questions for this session
                start_idx = i * questions_per_session
                end_idx = start_idx + questions_per_session if i < num_sessions - 1 else len(topic_questions)
                session_questions = topic_questions[start_idx:end_idx]
                
                # Calculate session importance (average of questions)
                session_importance = sum(
                    importance_scores.get(q, 0.5) for q in session_questions
                ) / max(len(session_questions), 1)
                
                session = StudySession(
                    topic=topic_name,
                    duration_minutes=int(minutes_per_session),
                    importance_score=round(session_importance, 3),
                    questions_to_cover=[q[:100] for q in session_questions],  # Truncate for display
                    day=current_day,
                    session_number=session_number
                )
                
                sessions.append(session)
                session_number += 1
                daily_study_time += minutes_per_session
        
        return sessions
    
    async def predict_important_questions(
        self,
        questions: List[str],
        importance_scores: Dict[str, float],
        top_n: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Predict most important questions for upcoming exam
        
        Args:
            questions: All questions
            importance_scores: Importance scores for questions
            top_n: Number of top questions to return
            
        Returns:
            List of top predicted questions with scores
        """
        # Sort questions by importance score
        scored_questions = [
            {
                'question': q,
                'importance_score': importance_scores.get(q, 0.0)
            }
            for q in questions
        ]
        
        scored_questions.sort(key=lambda x: x['importance_score'], reverse=True)
        
        # Return top N
        return scored_questions[:top_n]


# Singleton instance
study_planner = StudyPlannerService()
