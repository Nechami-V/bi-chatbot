import os
import uuid
from fastapi import Request, Response

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.chat import router as chat_router
from app.routes.health import router as health_router
STATE_CACHE = {}
def cache_get(key: str):
    return STATE_CACHE.get(key)

def cache_set(key: str, value: str):
    STATE_CACHE[key] = value

def cache_delete(key: str):
    STATE_CACHE.pop(key, None)

def create_app() -> FastAPI:
    SID_COOKIE_NAME = "sid"
    SID_MAX_AGE = 60 * 60 * 24 * 30  # 30 יום
    app = FastAPI(title="BI Chatbot Clean MVP")

    @app.middleware("http")
    async def ensure_sid_cookie(request: Request, call_next):
        sid = request.cookies.get(SID_COOKIE_NAME)

        response: Response = await call_next(request)

        if not sid:
            sid = str(uuid.uuid4())
            response.set_cookie(
                key=SID_COOKIE_NAME,
                value=sid,
                httponly=True,
                secure=False,   # ב-PROD על HTTPS לשנות ל-True
                samesite="Lax",
                max_age=SID_MAX_AGE,
            )

        return response

    allowed_origins = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000")
    if allowed_origins:
        origins = [origin.strip() for origin in allowed_origins.split(",") if origin.strip()]
    else:
        # Default dev origins to make local development easier
        origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://10.5.0.40:3000" # Your specific IP
        ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Expose routes both with and without /api prefix for frontend compatibility
    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(health_router, prefix="/api")
    app.include_router(chat_router, prefix="/api")
    return app

app = create_app()
