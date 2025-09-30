"""
BI Chatbot API - Main Application Entry Point

This FastAPI application powers the BI Chatbot system. It enables users to ask
business intelligence questions in Hebrew and receive intelligent answers based
on database analysis.

Key Capabilities
----------------
1. Hebrew natural language processing
2. Automatic SQL query generation
3. Database execution and results analysis
4. Natural language response generation
5. RESTful API with auto-generated documentation

Available Endpoints
-------------------
- GET  /          : Root endpoint with system info
- POST /ask       : Main chatbot endpoint
- GET  /health    : Health check endpoint
- Swagger UI      : /docs
- ReDoc           : /redoc

Author: BI Chatbot Team
Version: 2.0.0
"""

from fastapi import FastAPI, Depends
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

# Import API versioned routes
from app.api.v1.routes import router as v1_router

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
    version="2.0.0",
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


@app.get("/", tags=["System"])
def root():
    """Provide basic information about the service"""

    return {
        "name": "BI Chatbot API",
        "version": "2.0.0",
        "description": "AI-powered Business Intelligence Chatbot",
        "status": "active",
        "openai_configured": get_openai_key() != "api-key",
        "endpoints": {
            "chat": "/ask",
            "health": "/health",
            "docs": "/docs",
            "api_v1": "/api/v1",
        },
    }


@app.post("/ask", response_model=QueryResponse, tags=["Chatbot"])
async def ask_question(request: QueryRequest, db: Session = Depends(get_db)) -> QueryResponse:
    """Process a natural language question and return a structured response"""
    
    chatbot_service = ChatbotService(db)
    return await chatbot_service.process_question(request)


@app.get("/health", tags=["System"])
def health_check() -> dict:
    """Basic health check endpoint

    Returns information about system status and configuration.
    """

    return {
        "status": "healthy",
        "database": "connected",
        "openai_configured": get_openai_key() != "api-key",
        "version": "2.0.0",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8081)