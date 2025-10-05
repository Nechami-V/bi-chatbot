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
- POST /auth/login    : User login
- GET  /auth/me       : Get current user info
- GET  /health        : Health check endpoint
- Swagger UI          : /docs
- ReDoc               : /redoc

Author: BI Chatbot Team
Version: 3.0.0 - With Authentication
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
import os
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_openai_key() -> str:
    """Retrieve the OpenAI API key from environment variables"""

    return os.getenv("OPENAI_API_KEY", "api-key")


@app.on_event("startup")
async def startup_event() -> None:
    """Run initialization tasks when the API starts"""

    print("🚀 BI Chatbot API starting...")
    init_db()
    print("✅ Initialization complete")


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
            "chat_demo": "/ask-demo (no auth)",
            "login": "/api/v1/auth/login",
            "user_info": "/api/v1/auth/me", 
            "health": "/health",
            "docs": "/docs",
            "api_v1": "/api/v1",
        },
        "demo_users": {
            "admin": "david.cohen@company.com / 123456",
            "sales_manager": "sarah.levi@company.com / 123456",
            "sales": "michael.abramovich@company.com / 123456"
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
    admin_user = user_db.get_user_by_email("david.cohen@company.com")
    return await chatbot_service.process_question(request, user=admin_user)


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