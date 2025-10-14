"""
Chat routes for BI Chatbot API

Contains main chatbot endpoints for text-based conversations.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.chatbot_service import ChatbotService
from app.services.user_service import user_db
from app.api.auth import verify_token
from app.models.user import User
from app.schemas.chat import QueryRequest, QueryResponse

router = APIRouter()


@router.post("/ask", response_model=QueryResponse, tags=["Chatbot"])
async def ask_question(
    request: QueryRequest,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
) -> QueryResponse:
    """Process a natural language question with user authentication
    
    Requires valid JWT token in Authorization header.
    User permissions are checked before processing the question.
    """
    chatbot_service = ChatbotService(db)
    return await chatbot_service.process_question(request, user=current_user)


@router.post("/ask-demo", response_model=QueryResponse, tags=["Chatbot"])
async def ask_question_demo(
    request: QueryRequest,
    db: Session = Depends(get_db)
) -> QueryResponse:
    """Demo endpoint without authentication (for testing)"""
    chatbot_service = ChatbotService(db)
    # Use admin user for demo
    admin_user = user_db.get_user_by_email("nech397@gmail.com")
    if not admin_user:
        raise HTTPException(status_code=500, detail="Demo admin user not found")
    
    return await chatbot_service.process_question(request, user=admin_user)