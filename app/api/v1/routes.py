from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import os

# Import database and services
from app.db.database import get_db
from app.services.chatbot_service import ChatbotService

# Import shared schemas
from app.schemas.chat import QueryRequest, QueryResponse

# Create router
router = APIRouter()

def get_openai_key():
    """Get OpenAI API key from environment"""
    return os.getenv('OPENAI_API_KEY', 'api-key')

# API Endpoints
@router.get("/")
def root():
    return {
        "message": "BI Chatbot API v1.0 - AI Powered",
        "status": "active",
        "openai_key_configured": get_openai_key() != 'api-key'
    }

@router.post("/ask", response_model=QueryResponse)
async def ask_question_post(request: QueryRequest, db: Session = Depends(get_db)) -> QueryResponse:
    """Ask a question in natural language and get a response based on BI data with AI"""
    
    chatbot_service = ChatbotService(db)
    return await chatbot_service.process_question(request)

@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",
        "openai_key": get_openai_key() != 'api-key'
    }