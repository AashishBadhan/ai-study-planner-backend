"""
Vercel Serverless Function Handler
"""
from app.main import app

# Export for Vercel
handler = app
