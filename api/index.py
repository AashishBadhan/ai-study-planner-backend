"""
Vercel Serverless Entry Point - Ultra Minimal
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Create app
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "AI Study Planner API is running on Vercel!", "status": "ok"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/api/test")
def test():
    return {"test": "success", "platform": "vercel"}

