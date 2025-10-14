"""
System routes for BI Chatbot API

Contains endpoints for system information and health monitoring.
"""

import os
from fastapi import APIRouter
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()


def get_openai_key():
    """Get OpenAI API key from environment"""
    return os.getenv('OPENAI_API_KEY', 'api-key')


@router.get("/", tags=["System"])
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


@router.get("/health", tags=["System"])
def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "BI Chatbot API",
        "version": "3.0.0-auth"
    }