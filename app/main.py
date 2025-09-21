from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import from our new structure
from app.db.database import init_db
from app.api.v1.routes import router as api_v1_router

# Initialize FastAPI app
app = FastAPI(
    title="BI Chatbot API",
    description="API for natural language to BI queries",
    version="0.1.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers will create service instances as needed

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    # This will create tables and add sample data
    init_db()

# Request/Response models are defined in app/schemas/query.py

# Root endpoint
@app.get("/")
def root():
    return {
        "message": "BI Chatbot API is running",
        "endpoints": [
            {"path": "/api/v1/ask", "method": "GET", "description": "Ask a question in natural language"},
            {"path": "/api/v1/ask", "method": "POST", "description": "Ask a question in natural language (with JSON body)"}
        ]
    }

# Include API v1 routes
app.include_router(api_v1_router, prefix="/api/v1")
