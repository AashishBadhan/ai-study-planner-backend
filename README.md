# AI Study Planner - Backend

## Overview
Backend API for the AI Study Planner application. Built with FastAPI, MongoDB, and Hugging Face Transformers for intelligent exam preparation and study scheduling.

## Features

### 1. **Document Processing**
- Upload exam papers in PDF, image, or text format
- OCR text extraction using Tesseract
- Automatic question extraction and parsing

### 2. **NLP & Analysis**
- Question classification using BERT embeddings
- Topic extraction and clustering
- Repetition pattern detection
- Importance score calculation based on frequency and recency

### 3. **Study Planning**
- AI-powered study schedule generation
- Time allocation based on topic importance
- Personalized session planning

### 4. **Study Timer**
- Pomodoro technique implementation
- Configurable work/break intervals
- Real-time updates via WebSocket
- Session statistics tracking

## Tech Stack

- **Framework**: FastAPI
- **Database**: MongoDB (with Motor async driver)
- **ML/NLP**: 
  - Sentence Transformers (BERT)
  - scikit-learn
  - PyTorch
- **OCR**: Tesseract OCR, PyPDF2
- **Other**: Pydantic, Uvicorn

## Installation

### Prerequisites
- Python 3.9+
- MongoDB 4.4+
- Tesseract OCR

### Install Tesseract OCR

**Windows:**
```powershell
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
# Install and add to PATH
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

### Setup

1. **Clone the repository**
```powershell
cd "c:\Users\qq\Music\ne pro\ai-study-planner\backend"
```

2. **Create virtual environment**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3. **Install dependencies**
```powershell
pip install -r requirements.txt
```

4. **Configure environment**
```powershell
cp .env.example .env
# Edit .env with your settings
```

5. **Start MongoDB**
```powershell
# Make sure MongoDB is running
# Default: mongodb://localhost:27017
```

## Running the Server

### Development Mode
```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run with auto-reload
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## API Endpoints

### Upload & Processing
- `POST /api/upload/upload` - Upload exam paper
- `GET /api/upload/papers` - Get all papers
- `GET /api/upload/papers/{id}` - Get specific paper

### Analysis
- `GET /api/analysis/analysis` - Complete analysis
- `GET /api/analysis/questions` - Get questions
- `GET /api/analysis/topics` - Get topics
- `GET /api/analysis/similar-questions` - Find similar questions

### Schedule
- `POST /api/schedule/generate` - Generate study schedule
- `GET /api/schedule/schedules` - Get saved schedules
- `POST /api/schedule/predict-questions` - Predict important questions

### Timer
- `POST /api/timer/create` - Create timer
- `POST /api/timer/start` - Start timer
- `POST /api/timer/pause` - Pause timer
- `POST /api/timer/reset` - Reset timer
- `GET /api/timer/state` - Get timer state
- `GET /api/timer/stats` - Get session stats
- `WS /api/timer/ws/{user_id}` - WebSocket for real-time updates

## Example Usage

### 1. Upload a Paper
```python
import requests

url = "http://localhost:8000/api/upload/upload"
files = {"file": open("exam_paper.pdf", "rb")}
data = {"year": 2024, "subject": "Computer Science"}

response = requests.post(url, files=files, data=data)
print(response.json())
```

### 2. Get Analysis
```python
response = requests.get("http://localhost:8000/api/analysis/analysis")
analysis = response.json()

print(f"Total Questions: {analysis['total_questions']}")
print(f"Topics: {len(analysis['topics'])}")
print(f"Important Topics: {analysis['important_topics']}")
```

### 3. Generate Schedule
```python
schedule_request = {
    "available_hours": 40,
    "study_duration": 25,
    "break_duration": 5
}

response = requests.post(
    "http://localhost:8000/api/schedule/generate",
    json=schedule_request
)
schedule = response.json()

print(f"Total Sessions: {schedule['total_sessions']}")
print(f"Topic Distribution: {schedule['topic_distribution']}")
```

## Testing

```powershell
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_nlp_service.py -v
```

## Project Structure

```
backend/
├── app/
│   ├── api/              # API route handlers
│   │   ├── upload.py     # File upload endpoints
│   │   ├── analysis.py   # Analysis endpoints
│   │   ├── schedule.py   # Schedule endpoints
│   │   └── timer.py      # Timer endpoints
│   ├── models/           # Data models
│   │   ├── database.py   # Database models
│   │   └── schemas.py    # Pydantic schemas
│   ├── services/         # Business logic
│   │   ├── ocr_service.py      # OCR & text extraction
│   │   ├── nlp_service.py      # NLP processing
│   │   ├── study_planner.py    # Schedule generation
│   │   └── timer_service.py    # Timer management
│   ├── utils/            # Utility functions
│   ├── config.py         # Configuration
│   └── main.py           # FastAPI application
├── tests/                # Unit tests
├── uploads/              # Uploaded files storage
├── requirements.txt      # Python dependencies
└── .env.example          # Environment variables template
```

## Configuration

Edit `.env` file:

```env
# Database
DATABASE_URL=mongodb://localhost:27017
DATABASE_NAME=ai_study_planner

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=True

# Security
SECRET_KEY=your-secret-key-here

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# ML Model
MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
DEVICE=cpu
```

## Performance Tips

1. **Use GPU for NLP**: Set `DEVICE=cuda` in `.env` if GPU available
2. **Cache embeddings**: The service caches embeddings for better performance
3. **Batch processing**: Upload multiple papers together
4. **Database indexing**: Indexes are automatically created on startup

## Troubleshooting

### Tesseract not found
```powershell
# Set Tesseract path in ocr_service.py
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### MongoDB connection error
```powershell
# Check if MongoDB is running
# Start MongoDB service
net start MongoDB
```

### Memory issues with large PDFs
- Process PDFs in smaller chunks
- Increase available memory
- Use pagination for results

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## License

MIT License
