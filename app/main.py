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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load environment variables (expects .env file)
load_dotenv()

# Import database utilities and services
from app.db.database import init_db

# Import API routes
from app.api.system import router as system_router
from app.api.chat import router as chat_router
from app.api.voice import router as voice_router
from app.api.auth import router as auth_router


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


@app.on_event("startup")
async def startup_event() -> None:
    """Run initialization tasks when the API starts"""

    init_db()


# Mount all API routes
app.include_router(system_router, tags=["System"])
app.include_router(chat_router, tags=["Chat"])
app.include_router(voice_router, tags=["Voice"])
app.include_router(auth_router, tags=["Authentication"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8081)