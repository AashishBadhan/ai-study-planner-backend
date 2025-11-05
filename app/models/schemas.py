"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class FileType(str, Enum):
    """Supported file types"""
    PDF = "pdf"
    IMAGE = "image"
    TEXT = "text"


class QuestionBase(BaseModel):
    """Base schema for questions"""
    text: str
    topic: Optional[str] = None
    year: Optional[int] = None
    difficulty: Optional[str] = None


class QuestionCreate(QuestionBase):
    """Schema for creating a question"""
    pass


class Question(QuestionBase):
    """Schema for question response"""
    id: str
    importance_score: float = 0.0
    frequency: int = 1
    last_appeared: Optional[int] = None
    
    class Config:
        from_attributes = True


class TopicAnalysis(BaseModel):
    """Schema for topic analysis results"""
    topic: str
    frequency: int
    importance_score: float
    questions: List[str]
    avg_difficulty: Optional[str] = None


class PaperUploadResponse(BaseModel):
    """Response after uploading a paper"""
    success: bool
    message: str
    paper_id: str
    extracted_text_length: int
    questions_extracted: int
    topics_identified: List[str]


class StudyScheduleRequest(BaseModel):
    """Request to generate a study schedule"""
    available_hours: float = Field(..., gt=0, description="Total available study hours")
    start_date: Optional[datetime] = None
    exam_date: Optional[datetime] = None
    study_duration: int = Field(25, description="Study session duration in minutes")
    break_duration: int = Field(5, description="Break duration in minutes")
    topics_to_include: Optional[List[str]] = None
    
    @validator('available_hours')
    def validate_hours(cls, v):
        if v > 1000:
            raise ValueError('Available hours seems unreasonably high')
        return v


class StudySession(BaseModel):
    """Single study session in the schedule"""
    topic: str
    duration_minutes: int
    importance_score: float
    questions_to_cover: List[str]
    day: int
    session_number: int


class StudyScheduleResponse(BaseModel):
    """Generated study schedule response"""
    total_hours: float
    total_sessions: int
    sessions: List[StudySession]
    topic_distribution: Dict[str, float]  # topic -> hours allocated
    start_date: Optional[str] = None
    exam_date: Optional[str] = None


class TimerConfig(BaseModel):
    """Configuration for study timer"""
    study_duration: int = Field(25, description="Study duration in minutes")
    break_duration: int = Field(5, description="Break duration in minutes")
    long_break_duration: int = Field(15, description="Long break duration in minutes")
    sessions_until_long_break: int = Field(4, description="Number of sessions before long break")


class TimerState(BaseModel):
    """Current state of the study timer"""
    is_running: bool = False
    is_break: bool = False
    current_session: int = 0
    time_remaining: int = 0  # seconds
    topic: Optional[str] = None


class AnalysisResponse(BaseModel):
    """Complete analysis response"""
    total_questions: int
    topics: List[TopicAnalysis]
    repeated_questions: List[Dict[str, Any]]
    important_topics: List[str]
    predictions: List[Question]
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response schema"""
    success: bool = False
    error: str
    detail: Optional[str] = None


class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    database: str
    ml_model_loaded: bool
