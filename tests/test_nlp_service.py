"""
Unit tests for NLP Service
"""
import pytest
from app.services.nlp_service import NLPService


@pytest.fixture
async def nlp_service():
    """Create NLP service instance"""
    service = NLPService()
    await service.initialize()
    return service


@pytest.mark.asyncio
async def test_extract_questions(nlp_service):
    """Test question extraction from text"""
    text = """
    Q1. What is machine learning?
    Q2. Explain the concept of neural networks.
    Q3. Define supervised learning?
    """
    
    questions = await nlp_service.extract_questions(text)
    
    assert len(questions) >= 3
    assert any("machine learning" in q.lower() for q in questions)


@pytest.mark.asyncio
async def test_classify_questions(nlp_service):
    """Test question classification"""
    questions = [
        "What is machine learning?",
        "Explain neural networks",
        "Define supervised learning",
        "What is a binary tree?",
        "Explain sorting algorithms"
    ]
    
    topics = await nlp_service.classify_questions(questions, num_topics=2)
    
    assert len(topics) > 0
    assert all(isinstance(qs, list) for qs in topics.values())


@pytest.mark.asyncio
async def test_detect_similar_questions(nlp_service):
    """Test similar question detection"""
    questions = [
        "What is machine learning?",
        "Define machine learning",
        "What is a neural network?",
        "Explain neural networks"
    ]
    
    similar = await nlp_service.detect_similar_questions(questions, similarity_threshold=0.7)
    
    assert len(similar) > 0
    assert all('questions' in group for group in similar)
