import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Local imports
from app.db.database import init_db
from app.api.auth import router as auth_router


# Logger
logger = logging.getLogger(__name__)


# FastAPI app
app = FastAPI(
    title="BI Chatbot API",
    description="API for BI queries and authentication",
    version="0.1.0",
)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup
@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info("Application startup complete")


# Routers
app.include_router(auth_router)


# Health
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}


# Root
@app.get("/")
def root():
    return {
        "message": "BI Chatbot API is running",
        "endpoints": [
            {"path": "/auth/login", "method": "POST", "description": "Authenticate and get token"},
            {"path": "/auth/me", "method": "GET", "description": "Current user info"},
        ],
    }
