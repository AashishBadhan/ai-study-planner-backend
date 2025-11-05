"""
Database models and connection handlers
Supports both MongoDB and PostgreSQL
"""
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from datetime import datetime
from ..config import settings
import logging

logger = logging.getLogger(__name__)


class MongoDB:
    """MongoDB connection handler"""
    client: Optional[AsyncIOMotorClient] = None
    db = None
    
    @classmethod
    async def connect_db(cls):
        """Initialize database connection"""
        try:
            cls.client = AsyncIOMotorClient(settings.DATABASE_URL, serverSelectionTimeoutMS=5000)
            cls.db = cls.client[settings.DATABASE_NAME]
            
            # Test connection
            await cls.client.admin.command('ping')
            
            # Create indexes for better performance
            await cls.db.papers.create_index("uploaded_at")
            await cls.db.questions.create_index("topic")
            await cls.db.questions.create_index("importance_score")
            await cls.db.schedules.create_index("user_id")
            
            logger.info("MongoDB connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    @classmethod
    async def close_db(cls):
        """Close database connection"""
        if cls.client:
            cls.client.close()
            logger.info("MongoDB connection closed")
    
    @classmethod
    def get_collection(cls, name: str):
        """Get a collection from the database"""
        if cls.db is None:
            raise RuntimeError("Database not initialized")
        return cls.db[name]


# Database instance
db = MongoDB()


class Paper:
    """Paper document model"""
    
    @staticmethod
    async def create(file_name: str, file_type: str, extracted_text: str, 
                     questions: list, topics: list):
        """Create a new paper document"""
        collection = db.get_collection("papers")
        paper = {
            "file_name": file_name,
            "file_type": file_type,
            "extracted_text": extracted_text,
            "questions": questions,
            "topics": topics,
            "uploaded_at": datetime.utcnow(),
            "processed": True
        }
        result = await collection.insert_one(paper)
        paper["_id"] = str(result.inserted_id)
        return paper
    
    @staticmethod
    async def get_all():
        """Get all papers"""
        collection = db.get_collection("papers")
        papers = []
        async for paper in collection.find():
            paper["_id"] = str(paper["_id"])
            papers.append(paper)
        return papers
    
    @staticmethod
    async def get_by_id(paper_id: str):
        """Get paper by ID"""
        collection = db.get_collection("papers")
        from bson import ObjectId
        paper = await collection.find_one({"_id": ObjectId(paper_id)})
        if paper:
            paper["_id"] = str(paper["_id"])
        return paper


class QuestionDB:
    """Question document model"""
    
    @staticmethod
    async def create(text: str, topic: str, year: Optional[int] = None,
                     importance_score: float = 0.0):
        """Create a new question"""
        collection = db.get_collection("questions")
        question = {
            "text": text,
            "topic": topic,
            "year": year,
            "importance_score": importance_score,
            "frequency": 1,
            "created_at": datetime.utcnow()
        }
        result = await collection.insert_one(question)
        question["_id"] = str(result.inserted_id)
        return question
    
    @staticmethod
    async def get_all():
        """Get all questions"""
        collection = db.get_collection("questions")
        questions = []
        async for question in collection.find():
            question["_id"] = str(question["_id"])
            questions.append(question)
        return questions
    
    @staticmethod
    async def get_by_topic(topic: str):
        """Get questions by topic"""
        collection = db.get_collection("questions")
        questions = []
        async for question in collection.find({"topic": topic}):
            question["_id"] = str(question["_id"])
            questions.append(question)
        return questions
    
    @staticmethod
    async def update_importance(question_id: str, importance_score: float):
        """Update question importance score"""
        collection = db.get_collection("questions")
        from bson import ObjectId
        await collection.update_one(
            {"_id": ObjectId(question_id)},
            {"$set": {"importance_score": importance_score}}
        )


class Schedule:
    """Study schedule document model"""
    
    @staticmethod
    async def create(user_id: str, schedule_data: dict):
        """Create a new schedule"""
        collection = db.get_collection("schedules")
        schedule = {
            "user_id": user_id,
            "schedule_data": schedule_data,
            "created_at": datetime.utcnow()
        }
        result = await collection.insert_one(schedule)
        schedule["_id"] = str(result.inserted_id)
        return schedule
    
    @staticmethod
    async def get_by_user(user_id: str):
        """Get schedules for a user"""
        collection = db.get_collection("schedules")
        schedules = []
        async for schedule in collection.find({"user_id": user_id}):
            schedule["_id"] = str(schedule["_id"])
            schedules.append(schedule)
        return schedules
