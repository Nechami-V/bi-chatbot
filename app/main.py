import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Local imports
from app.db.database import init_db
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.system import router as system_router
from app.api.voice import router as voice_router


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


# Routers (base paths)
app.include_router(system_router)
app.include_router(chat_router)
app.include_router(voice_router)
app.include_router(auth_router)

# Compatibility aliases for existing frontend paths
# Expose same routes under /chat and /api/chat
app.include_router(chat_router, prefix="/chat")
app.include_router(chat_router, prefix="/api/chat")

# Expose auth under /api as well (auth router already has /auth prefix)
app.include_router(auth_router, prefix="/api")

# Expose system and voice under /api as well
app.include_router(system_router, prefix="/api")
app.include_router(voice_router, prefix="/api")


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
            {"path": "/ask", "method": "POST", "description": "Chat question (uses PACK if set)"},
            {"path": "/chat/ask", "method": "POST", "description": "Chat alias"},
            {"path": "/api/chat/ask", "method": "POST", "description": "Chat alias under /api"},
        ],
    }
