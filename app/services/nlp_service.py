"""
NLP Service for Question Classification and Topic Extraction
Uses transformer models for semantic understanding
"""
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.cluster import KMeans, DBSCAN
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    
import re
from typing import List, Dict, Tuple, Any
import logging
from collections import Counter, defaultdict
from ..config import settings

logger = logging.getLogger(__name__)


class NLPService:
    """Service for NLP tasks like question classification and topic extraction"""
    
    def __init__(self):
        """Initialize NLP models"""
        self.model = None
        self.embeddings_cache = {}
        
    async def initialize(self):
        """Load pre-trained models"""
        if not ML_AVAILABLE:
            logger.warning("ML libraries not available. NLP features will be limited.")
            return
            
        try:
            logger.info(f"Loading model: {settings.MODEL_NAME}")
            self.model = SentenceTransformer(settings.MODEL_NAME)
            logger.info("NLP model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load NLP model: {e}")
            # Don't raise - allow app to work without ML features
            logger.warning("App will run with limited NLP features")
    
    async def extract_questions(self, text: str) -> List[str]:
        """
        Extract individual questions from text
        
        Args:
            text: Raw extracted text
            
        Returns:
            List of question strings
        """
        # Split by question markers
        questions = []
        
        # Pattern 1: Question numbers (Q1, Q.1, 1., etc.)
        pattern1 = r'(?:Q\.?\s*\d+|Question\s*\d+|\d+\.|^\d+\))'
        
        # Pattern 2: Questions ending with ?
        # Split text into potential questions
        lines = text.split('\n')
        current_question = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line starts with question marker
            if re.match(pattern1, line, re.IGNORECASE):
                # Save previous question
                if current_question:
                    q_text = ' '.join(current_question).strip()
                    if len(q_text) > 10:  # Minimum question length
                        questions.append(q_text)
                current_question = [line]
            else:
                current_question.append(line)
        
        # Add last question
        if current_question:
            q_text = ' '.join(current_question).strip()
            if len(q_text) > 10:
                questions.append(q_text)
        
        # Also find questions ending with ?
        question_mark_pattern = r'[^.!?]*\?'
        for match in re.finditer(question_mark_pattern, text):
            q = match.group().strip()
            if len(q) > 20 and q not in questions:
                questions.append(q)
        
        # Clean up questions
        questions = [self._clean_question(q) for q in questions]
        questions = [q for q in questions if len(q) > 15]  # Filter very short questions
        
        logger.info(f"Extracted {len(questions)} questions")
        return questions
    
    def _clean_question(self, question: str) -> str:
        """Clean and normalize question text"""
        # Remove question numbers
        question = re.sub(r'^(?:Q\.?\s*\d+|Question\s*\d+|\d+\.|\d+\))\s*', '', question, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        question = ' '.join(question.split())
        
        # Remove marks/points indicators
        question = re.sub(r'\[\s*\d+\s*marks?\s*\]', '', question, flags=re.IGNORECASE)
        question = re.sub(r'\(\s*\d+\s*marks?\s*\)', '', question, flags=re.IGNORECASE)
        
        return question.strip()
    
    async def classify_questions(self, questions: List[str], num_topics: int = 10) -> Dict[str, List[str]]:
        """
        Classify questions into topics using clustering
        
        Args:
            questions: List of question strings
            num_topics: Number of topics to identify
            
        Returns:
            Dictionary mapping topic names to lists of questions
        """
        if not questions:
            return {}
        
        # If ML not available, use simple keyword-based classification
        if not ML_AVAILABLE or self.model is None:
            logger.warning("Using fallback keyword-based classification")
            return await self._keyword_based_classification(questions)
        
        try:
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(questions)} questions")
            embeddings = self.model.encode(questions, show_progress_bar=False)
            
            # Determine optimal number of clusters
            n_clusters = min(num_topics, len(questions))
            
            # Cluster questions
            if len(questions) > n_clusters:
                kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                labels = kmeans.fit_predict(embeddings)
            else:
                labels = list(range(len(questions)))
            
            # Group questions by cluster
            topic_questions = defaultdict(list)
            for idx, label in enumerate(labels):
                topic_questions[f"Topic_{label}"].append(questions[idx])
            
            # Extract topic names from representative questions
            named_topics = {}
            for topic_id, topic_qs in topic_questions.items():
                topic_name = await self._extract_topic_name(topic_qs)
                named_topics[topic_name] = topic_qs
            
            logger.info(f"Classified into {len(named_topics)} topics")
            return named_topics
            
        except Exception as e:
            logger.error(f"Question classification error: {e}")
            return {"General": questions}
    
    async def _keyword_based_classification(self, questions: List[str]) -> Dict[str, List[str]]:
        """Fallback keyword-based classification when ML is not available"""
        topic_keywords = {
            'Algorithms': ['algorithm', 'sorting', 'searching', 'complexity'],
            'Data Structures': ['array', 'linked list', 'tree', 'graph', 'stack', 'queue'],
            'Databases': ['database', 'sql', 'query', 'table', 'relation'],
            'Networking': ['network', 'protocol', 'tcp', 'ip', 'osi'],
            'Operating Systems': ['process', 'thread', 'memory', 'cpu', 'scheduling'],
            'Programming': ['code', 'function', 'class', 'variable', 'loop'],
            'Mathematics': ['calculus', 'algebra', 'equation', 'probability', 'statistics'],
        }
        
        classified = defaultdict(list)
        unclassified = []
        
        for question in questions:
            q_lower = question.lower()
            matched = False
            
            for topic, keywords in topic_keywords.items():
                if any(kw in q_lower for kw in keywords):
                    classified[topic].append(question)
                    matched = True
                    break
            
            if not matched:
                unclassified.append(question)
        
        if unclassified:
            classified['General'] = unclassified
        
        return dict(classified)
    
    async def _extract_topic_name(self, questions: List[str]) -> str:
        """
        Extract a meaningful topic name from a list of questions
        Uses keyword extraction from the questions
        """
        # Combine all questions
        combined_text = ' '.join(questions).lower()
        
        # Common academic subject keywords
        topic_keywords = {
            'algorithm': 'Algorithms',
            'data structure': 'Data Structures',
            'database': 'Databases',
            'network': 'Networking',
            'operating system': 'Operating Systems',
            'software': 'Software Engineering',
            'web': 'Web Development',
            'security': 'Security',
            'machine learning': 'Machine Learning',
            'ai': 'Artificial Intelligence',
            'calculus': 'Calculus',
            'algebra': 'Algebra',
            'probability': 'Probability',
            'statistics': 'Statistics',
            'physics': 'Physics',
            'chemistry': 'Chemistry',
            'biology': 'Biology',
            'programming': 'Programming',
            'java': 'Java Programming',
            'python': 'Python Programming',
            'c++': 'C++ Programming',
        }
        
        # Check for keyword matches
        for keyword, topic_name in topic_keywords.items():
            if keyword in combined_text:
                return topic_name
        
        # Extract most common significant words
        words = re.findall(r'\b[a-z]{4,}\b', combined_text)
        stop_words = {'what', 'which', 'where', 'when', 'explain', 'describe', 'define', 
                      'discuss', 'compare', 'with', 'that', 'this', 'from', 'have', 'been'}
        words = [w for w in words if w not in stop_words]
        
        if words:
            common_words = Counter(words).most_common(2)
            topic_name = ' '.join([w[0].capitalize() for w in common_words])
            return topic_name
        
        return "General Topic"
    
    async def detect_similar_questions(self, questions: List[str], 
                                       similarity_threshold: float = 0.8) -> List[Dict[str, Any]]:
        """
        Detect repeated or highly similar questions
        
        Args:
            questions: List of question strings
            similarity_threshold: Cosine similarity threshold (0-1)
            
        Returns:
            List of similar question groups
        """
        if len(questions) < 2:
            return []
        
        # If ML not available, use simple text matching
        if not ML_AVAILABLE or self.model is None:
            logger.warning("Using fallback text-based similarity detection")
            return self._text_based_similarity(questions)
        
        try:
            # Generate embeddings
            embeddings = self.model.encode(questions, show_progress_bar=False)
            
            # Calculate pairwise similarities
            similarities = cosine_similarity(embeddings)
            
            # Find similar pairs
            similar_groups = []
            processed = set()
            
            for i in range(len(questions)):
                if i in processed:
                    continue
                
                group = [i]
                for j in range(i + 1, len(questions)):
                    if j not in processed and similarities[i][j] >= similarity_threshold:
                        group.append(j)
                        processed.add(j)
                
                if len(group) > 1:
                    similar_groups.append({
                        'questions': [questions[idx] for idx in group],
                        'indices': group,
                        'similarity': float(np.mean([similarities[i][j] for j in group[1:]]))
                    })
                    processed.add(i)
            
            logger.info(f"Found {len(similar_groups)} groups of similar questions")
            return similar_groups
            
        except Exception as e:
            logger.error(f"Similar question detection error: {e}")
            return []
    
    def _text_based_similarity(self, questions: List[str]) -> List[Dict[str, Any]]:
        """Fallback text-based similarity when ML is not available"""
        similar_groups = []
        processed = set()
        
        for i in range(len(questions)):
            if i in processed:
                continue
            
            group = [i]
            q1_words = set(questions[i].lower().split())
            
            for j in range(i + 1, len(questions)):
                if j not in processed:
                    q2_words = set(questions[j].lower().split())
                    # Jaccard similarity
                    intersection = len(q1_words & q2_words)
                    union = len(q1_words | q2_words)
                    similarity = intersection / union if union > 0 else 0
                    
                    if similarity >= 0.5:  # Lower threshold for text-based
                        group.append(j)
                        processed.add(j)
            
            if len(group) > 1:
                similar_groups.append({
                    'questions': [questions[idx] for idx in group],
                    'indices': group,
                    'similarity': 0.7  # Approximate
                })
                processed.add(i)
        
        return similar_groups
    
    async def calculate_importance_scores(self, questions: List[str], 
                                          topics: Dict[str, List[str]],
                                          years: List[int] = None) -> Dict[str, float]:
        """
        Calculate importance scores for questions based on:
        - Frequency (how often it appears)
        - Recency (when it last appeared)
        - Topic clustering strength
        
        Args:
            questions: List of all questions
            topics: Topic classification results
            years: Optional list of years for each question
            
        Returns:
            Dictionary mapping question to importance score (0-1)
        """
        scores = {}
        
        # Calculate frequency scores
        similar_groups = await self.detect_similar_questions(questions, similarity_threshold=0.75)
        frequency_map = defaultdict(int)
        
        for group in similar_groups:
            for q_idx in group['indices']:
                frequency_map[questions[q_idx]] += len(group['indices'])
        
        # Normalize frequency scores
        max_freq = max(frequency_map.values()) if frequency_map else 1
        
        for i, question in enumerate(questions):
            # Base score from frequency
            freq_score = frequency_map.get(question, 1) / max_freq
            
            # Recency score (if years provided)
            recency_score = 0.5  # Default
            if years and i < len(years) and years[i]:
                current_year = 2025  # Or get dynamically
                year_diff = current_year - years[i]
                recency_score = max(0, 1 - (year_diff / 10))  # Decay over 10 years
            
            # Topic centrality score
            topic_score = 0.5  # Default
            for topic_name, topic_qs in topics.items():
                if question in topic_qs:
                    # Questions in larger topics get higher scores
                    topic_score = min(1.0, len(topic_qs) / (len(questions) / len(topics)))
                    break
            
            # Combined importance score (weighted average)
            importance = (
                0.4 * freq_score +
                0.3 * recency_score +
                0.3 * topic_score
            )
            
            scores[question] = round(importance, 3)
        
        return scores


# Singleton instance
nlp_service = NLPService()
