"""
In-Memory Database (No MongoDB needed)
Temporary storage - data lost on restart
"""
from typing import Optional, List, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MemoryDB:
    """In-memory database storage"""
    
    def __init__(self):
        self.papers: List[Dict] = []
        self.questions: List[Dict] = []
        self.schedules: List[Dict] = []
        self._next_id = 1
    
    def get_next_id(self) -> str:
        """Get next unique ID"""
        id_str = str(self._next_id)
        self._next_id += 1
        return id_str
    
    async def connect_db(self):
        """Initialize in-memory database"""
        logger.info("Using in-memory database (no MongoDB needed)")
        logger.warning("Data will be lost when server restarts!")
    
    async def close_db(self):
        """Clear in-memory database"""
        self.papers.clear()
        self.questions.clear()
        self.schedules.clear()
        logger.info("In-memory database cleared")


# Global instance
memory_db = MemoryDB()


class Paper:
    """Paper document model"""
    
    @staticmethod
    async def create(file_name: str, file_type: str, extracted_text: str, 
                     questions: list, topics: list):
        """Create a new paper"""
        paper = {
            "_id": memory_db.get_next_id(),
            "file_name": file_name,
            "file_type": file_type,
            "extracted_text": extracted_text,
            "questions": questions,
            "topics": topics,
            "uploaded_at": datetime.utcnow(),
            "processed": True
        }
        memory_db.papers.append(paper)
        return paper
    
    @staticmethod
    async def get_all():
        """Get all papers"""
        return memory_db.papers.copy()
    
    @staticmethod
    async def get_by_id(paper_id: str):
        """Get paper by ID"""
        for paper in memory_db.papers:
            if paper["_id"] == paper_id:
                return paper
        return None


class QuestionDB:
    """Question document model"""
    
    @staticmethod
    async def create(text: str, topic: str, year: Optional[int] = None,
                     importance_score: float = 0.0):
        """Create a new question"""
        question = {
            "_id": memory_db.get_next_id(),
            "text": text,
            "topic": topic,
            "year": year,
            "importance_score": importance_score,
            "frequency": 1,
            "created_at": datetime.utcnow()
        }
        memory_db.questions.append(question)
        return question
    
    @staticmethod
    async def get_all():
        """Get all questions"""
        return memory_db.questions.copy()
    
    @staticmethod
    async def get_by_topic(topic: str):
        """Get questions by topic"""
        return [q for q in memory_db.questions if q["topic"] == topic]
    
    @staticmethod
    async def update_importance(question_id: str, importance_score: float):
        """Update question importance score"""
        for question in memory_db.questions:
            if question["_id"] == question_id:
                question["importance_score"] = importance_score
                break


class Schedule:
    """Study schedule document model"""
    
    @staticmethod
    async def create(user_id: str, schedule_data: dict):
        """Create a new schedule"""
        schedule = {
            "_id": memory_db.get_next_id(),
            "user_id": user_id,
            "schedule_data": schedule_data,
            "created_at": datetime.utcnow()
        }
        memory_db.schedules.append(schedule)
        return schedule
    
    @staticmethod
    async def get_by_user(user_id: str):
        """Get schedules for a user"""
        return [s for s in memory_db.schedules if s["user_id"] == user_id]
