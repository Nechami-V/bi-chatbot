from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import database and services
from app.db.database import init_db, get_db
from app.services.translation_service import TranslationDictionary
from app.services.ai_service import AIService

# Import API routes
from app.api.v1.routes import router as v1_router

# Initialize FastAPI app
app = FastAPI(
    title="BI Chatbot API",
    description="API for natural language to BI queries with AI",
    version="2.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_openai_key():
    """Get OpenAI API key from environment"""
    return os.getenv('OPENAI_API_KEY', 'api-key')

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

# Include API routes
app.include_router(v1_router, prefix="/api/v1", tags=["v1"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)