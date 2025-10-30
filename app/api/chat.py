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
from app.schemas.chat import QueryRequest, QueryResponse, PackResponse
from app.services.ai_service import AIService
from app.simple_config import config

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


# Demo endpoint removed - use proper authentication


@router.post("/ask-pack", response_model=PackResponse, tags=["Chatbot"])
async def ask_question_pack(
    request: QueryRequest,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
) -> PackResponse:
    """Process a question using PACK-based prompts and return a unified JSON.

    Requires PACK to be set in environment/config. Returns 400 if not configured.
    """
    if not config.PACK:
        raise HTTPException(status_code=400, detail="PACK is not configured. Set PACK in environment.")

    ai = AIService(db)
    out = ai.generate_pack_output(request.question)
    return PackResponse(**{
        "short_answer": out.get("short_answer", ""),
        "sql_export": out.get("sql_export", ""),
        "sql_ratio": out.get("sql_ratio", ""),
    })
