from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

# Import database and AI processor
from app.db.database import init_db, get_db
from app.services.ai_processor import AIQuestionProcessor

# Request/Response models
class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    question: str
    answer: str
    sql: Optional[str] = None
    error: Optional[str] = None

# Initialize AI Processor (will be initialized per request with db session)

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

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    # This will create tables and add sample data
    init_db()
    logger.info("Application startup complete")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

# Define request/response models
class QueryResponse(BaseModel):
    question: str
    response: str
    sql: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    visualization: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    request_id: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class APIKeyCreate(BaseModel):
    description: Optional[str] = Field(None, description="Optional description for the API key")

class APIKeyResponse(BaseModel):
    key: str
    description: Optional[str] = None
    created_at: str
    last_used_at: Optional[str] = None

# Authentication endpoints
@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # This is a placeholder - implement proper user authentication
    # For now, we'll just accept any username/password in development
    if not config.DEBUG:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="User authentication not yet implemented"
        )
    
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# API key management endpoints
@app.post("/api-keys/", response_model=APIKeyResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    # In a real app, verify the API key has permission to create new keys
    new_key = create_api_key(
        user_id=1,  # Get from authenticated user in a real app
        db=db,
        description=key_data.description
    )
    
    return {
        "key": new_key,
        "description": key_data.description,
        "created_at": datetime.utcnow().isoformat(),
        "last_used_at": None
    }

# API endpoints
@app.get(
    "/ask", 
    response_model=QueryResponse,
    summary="Ask a question in natural language",
    description="""
    Ask a question in natural language and get a response with data.
    The system will generate and execute the appropriate SQL query.
    """
)
async def ask_question_get(
    question: str,
    request: Request,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
) -> QueryResponse:
    try:
        # Log the request
        logger.info(f"Processing question: {question[:200]}...")
        
        # Initialize the AI processor
        ai_processor = SmartAIProcessor(db)
        
        # Process the question
        start_time = time.time()
        result = await ai_processor.process_question(question)
        process_time = time.time() - start_time
        
        # Log the SQL query if it exists
        if 'sql' in result:
            sql_logger.log_query(
                query=result['sql'],
                params={},
                duration=process_time
            )
        
        if not result.get('success', False):
            error_msg = result.get('error', 'Failed to process question')
            logger.error(f"Error processing question: {error_msg}")
            
            return QueryResponse(
                question=question,
                response="אירעה שגיאה בעיבוד השאלה. אנא נסה שוב או פנה לתמיכה.",
                error=error_msg if config.DEBUG else None,
                request_id=request.state.request_id
            )
            
        logger.info(f"Successfully processed question in {process_time:.2f} seconds")
            
        return QueryResponse(
            question=question,
            response=result.get('response', ''),
            sql=result.get('sql') if config.DEBUG else None,
            data=result.get('data', []),
            visualization=result.get('visualization'),
            request_id=request.state.request_id
        )
        
    except Exception as e:
        logger.exception(f"Unexpected error processing question: {str(e)}")
        
        return QueryResponse(
            question=question,
            response="אירעה שגיאה בלתי צפויה. אנא נסה שוב מאוחר יותר.",
            error=str(e) if config.DEBUG else None,
            request_id=getattr(request.state, 'request_id', None)
        )

# Alias POST to GET for /ask
@app.post("/ask", response_model=QueryResponse, include_in_schema=False)
async def ask_question_post(
    question: str,
    request: Request,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
) -> QueryResponse:
    return await ask_question_get(question, request, db, api_key)

# Root endpoint
@app.get("/")
def root():
    return {
        "message": "BI Chatbot API is running",
        "endpoints": [
            {"path": "/ask", "method": "GET", "description": "Ask a question in natural language"},
            {"path": "/ask", "method": "POST", "description": "Ask a question in natural language (with JSON body)"}
        ]
    }

@app.post("/ask", response_model=QueryResponse)
async def ask_question_post(request: QueryRequest, db: Session = Depends(get_db)) -> QueryResponse:
    """Ask a question in natural language (POST) with JSON body."""
    return ask_question_get(request.question, request, db)
