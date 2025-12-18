"""
Chat routes for BI Chatbot API

Contains main chatbot endpoints for text-based conversations.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.auth import verify_token
from app.db.database import get_db
from app.models.user import User
from app.schemas.chat import PackResponse, QueryRequest, QueryResponse
from app.services.ai_service import AIService
from app.services.chatbot_service import ChatbotService
from app.services.export_service import ExportService
from app.simple_config import config

ALLOWED_EXPORT_FORMATS = ("excel", "csv")


router = APIRouter()


def _resolve_client_id(current_user: User) -> str:
    """Return the tenant/client identifier for the logged-in user or fallback."""
    return getattr(current_user, "client_id", None) or "KT"


@router.post("/ask", response_model=QueryResponse, tags=["Chatbot"])
async def ask_question(
    request: QueryRequest,
    current_user: User = Depends(verify_token),  # verify_token handles DISABLE_AUTH internally
    db: Session = Depends(get_db)
) -> QueryResponse:
    """Process a natural language question with user authentication
    
    If DISABLE_AUTH=true, authentication is bypassed.
    Otherwise, requires valid JWT token in Authorization header.
    """
    client_id = _resolve_client_id(current_user)
    chatbot_service = ChatbotService(db, client_id=client_id)
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
    If DISABLE_AUTH=true, authentication is bypassed.
    """
    if not config.PACK:
        raise HTTPException(status_code=400, detail="PACK is not configured. Set PACK in environment.")

    client_id = _resolve_client_id(current_user)
    ai = AIService(db, client_id=client_id)
    out = ai.generate_pack_output(request.question)
    return PackResponse(**{
        "short_answer": out.get("short_answer", ""),
        "sql_export": out.get("sql_export", ""),
        "sql_ratio": out.get("sql_ratio", ""),
    })


@router.post("/export", tags=["Export"])
async def export_data(
    request: QueryRequest,
    export_format: str = "excel",
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Export data to Excel or CSV based on natural language question
    
    Uses Exports.yaml prompt to generate optimized export SQL.
    Returns file ready for download.
    If DISABLE_AUTH=true, authentication is bypassed.
    
    Args:
        request: QueryRequest with question field
    export_format: "excel" or "csv" (default: "excel")
        
    Returns:
        File download response with appropriate content type
    """
    if export_format not in ALLOWED_EXPORT_FORMATS:
        raise HTTPException(status_code=400, detail="Format must be 'excel' or 'csv'")
    
    try:
        client_id = _resolve_client_id(current_user)
        export_service = ExportService(db, client_id=client_id)
        file_content, filename = export_service.export_data(
            question=request.question,
            format=export_format
        )
        
        # Set appropriate content type and headers
        if export_format == "excel":
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            media_type = "text/csv"
        
        return Response(
            content=file_content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

