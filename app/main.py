"""
BI Chatbot API - Main Application Entry Point with Authentication

This FastAPI application powers the BI Chatbot system with user authentication
and permissions. It enables authorized users to ask business intelligence 
questions in Hebrew and receive intelligent answers based on database analysis.

Key Capabilities
----------------
1. User authentication with JWT tokens
2. Permission-based access control
3. Hebrew natural language processing
4. Automatic SQL query generation
5. Database execution and results analysis
6. Natural language response generation
7. RESTful API with auto-generated documentation

Available Endpoints
-------------------
- GET  /              : Root endpoint with system info
- POST /ask           : Main chatbot endpoint (authenticated)
- POST /voice-query   : Voice chatbot endpoint (audio files, authenticated)
- POST /ask-demo      : Demo chatbot endpoint (no authentication)
- POST /auth/login    : User login
- GET  /auth/me       : Get current user info
- GET  /health        : Health check endpoint
- Swagger UI          : /docs
- ReDoc               : /redoc

Author: BI Chatbot Team
Version: 3.0.0 - With Authentication
"""

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
import os
import tempfile
import openai
from dotenv import load_dotenv

# Load environment variables (expects .env file)
load_dotenv()

# Import database utilities and services
from app.db.database import init_db, get_db
from app.services.chatbot_service import ChatbotService
from app.services.user_service import user_db

# Import API versioned routes
from app.api.v1.routes import router as v1_router
from app.api.v1.auth_routes import router as auth_router, verify_token

# Import models  
from app.models.user import User

# Import shared schemas
from app.schemas.chat import QueryRequest, QueryResponse


app = FastAPI(
    title="BI Chatbot API",
    description=(
        """AI-powered Business Intelligence Chatbot API.\n\n"
        "Ask business questions in Hebrew and receive intelligent answers "
        "based on database analysis. The system uses advanced AI models to "
        "understand natural language, generate SQL, execute queries, and "
        "produce natural language responses."""
    ),
    version="3.0.0-auth",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Enable CORS (update allow_origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000", 
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "null"  # For file:// protocol
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Additional CORS handling for complex requests
@app.middleware("http")
async def cors_handler(request: Request, call_next):
    # Handle preflight OPTIONS requests
    if request.method == "OPTIONS":
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
        }
        return Response(headers=headers)
    
    # Process the request
    try:
        response = await call_next(request)
        
        # Add CORS headers to response
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response
    except Exception as e:
        # Return error with CORS headers
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true",
            }
        )


def get_openai_key() -> str:
    """Retrieve the OpenAI API key from environment variables"""

    return os.getenv("OPENAI_API_KEY", "api-key")


async def transcribe_audio(audio_file: UploadFile) -> str:
    """Transcribe audio file using OpenAI Whisper API
    
    Args:
        audio_file: Uploaded audio file (MP3, WAV, etc.)
        
    Returns:
        str: Transcribed text in Hebrew
        
    Raises:
        HTTPException: If transcription fails
    """
    # Validate file type (be more flexible for WebM from browser)
    valid_types = ['audio/', 'video/webm', 'video/mp4']  # WebM often shows as video/webm
    if not audio_file.content_type or not any(audio_file.content_type.startswith(t) for t in valid_types):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {audio_file.content_type}. Please upload an audio file."
        )
    
    # Validate file size (max 25MB for Whisper API)
    max_size = 25 * 1024 * 1024  # 25MB
    audio_content = await audio_file.read()
    if len(audio_content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum size is 25MB."
        )
    
    try:
        # Create temporary file for the audio with appropriate extension
        file_extension = ".webm" if "webm" in audio_file.content_type else ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(audio_content)
            temp_file_path = temp_file.name
        
        # Configure OpenAI client
        openai_api_key = get_openai_key()
        if openai_api_key == "api-key":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenAI API key not configured"
            )
        
        client = openai.OpenAI(api_key=openai_api_key)
        
        # Transcribe audio using Whisper
        with open(temp_file_path, "rb") as audio_data:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_data,
                language="he"  # Hebrew language code
            )
        
        # Clean up temporary file
        os.unlink(temp_file_path)
        
        transcribed_text = transcript.text.strip()
        
        if not transcribed_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not transcribe audio. Please ensure the audio contains clear speech."
            )
        
        return transcribed_text
        
    except Exception as e:
        # Clean up temporary file if it exists
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        
        if isinstance(e, HTTPException):
            raise
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio transcription failed: {str(e)}"
        )


@app.on_event("startup")
async def startup_event() -> None:
    """Run initialization tasks when the API starts"""

    init_db()


# Mount versioned API routes
app.include_router(v1_router, prefix="/api/v1", tags=["API v1"])
app.include_router(auth_router, prefix="/api/v1", tags=["Authentication"])


@app.get("/", tags=["System"])
def root():
    """Provide basic information about the service"""

    return {
        "name": "BI Chatbot API",
        "version": "3.0.0-auth",
        "description": "AI-powered Business Intelligence Chatbot",
        "status": "active",
        "openai_configured": get_openai_key() != "api-key",
        "endpoints": {
            "chat": "/ask (authenticated)",
            "voice_chat": "/voice-query (authenticated, audio files)",
            "chat_demo": "/ask-demo (no auth)",
            "login": "/api/v1/auth/login",
            "user_info": "/api/v1/auth/me", 
            "health": "/health",
            "docs": "/docs",
            "api_v1": "/api/v1",
        },
        "demo_users": {
            "admin": "nech397@gmail.com / 1123456",
            "sales_manager": "sarah.levi@company.com / 1123456",
            "sales": "michael.abramovich@company.com / 1123456"
        }
    }


@app.post("/ask", response_model=QueryResponse, tags=["Chatbot"])
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


@app.post("/ask-demo", response_model=QueryResponse, tags=["Chatbot"])
async def ask_question_demo(
    request: QueryRequest,
    db: Session = Depends(get_db)
) -> QueryResponse:
    """Demo endpoint without authentication (for testing)"""
    
    chatbot_service = ChatbotService(db)
    # Use admin user for demo
    admin_user = user_db.get_user_by_email("nech397@gmail.com")
    return await chatbot_service.process_question(request, user=admin_user)


@app.post("/voice-query", response_model=QueryResponse, tags=["Chatbot"])
async def voice_query(
    audio_file: UploadFile = File(..., description="Audio file (MP3, WAV, etc.) to transcribe"),
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
) -> QueryResponse:
    """Process a voice question by transcribing audio and analyzing the text
    
    This endpoint:
    1. Receives an audio file (MP3, WAV, etc.)
    2. Transcribes it to Hebrew text using OpenAI Whisper
    3. Processes the transcribed text using the same logic as /ask endpoint
    4. Returns the same response format with additional transcription info
    
    Requires valid JWT token in Authorization header.
    User permissions are checked before processing the question.
    Maximum file size: 25MB
    """
    
    # Step 1: Transcribe the audio file
    transcribed_text = await transcribe_audio(audio_file)
    
    # Step 2: Create a QueryRequest with the transcribed text
    query_request = QueryRequest(question=transcribed_text)
    
    # Step 3: Process the question using existing chatbot service
    chatbot_service = ChatbotService(db)
    response = await chatbot_service.process_question(query_request, user=current_user)
    
    # Step 4: Add transcription info to response (modify answer to include it)
    if response.error is None:
        response.answer = f"🎙️ תמלול: \"{transcribed_text}\"\n\n{response.answer}"
    
    return response


@app.get("/health", tags=["System"])
def health_check() -> dict:
    """Basic health check endpoint

    Returns information about system status and configuration.
    """

    return {
        "status": "healthy",
        "database": "connected",
        "openai_configured": get_openai_key() != "api-key",
        "version": "3.0.0-auth",
        "authentication": "enabled"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8081)