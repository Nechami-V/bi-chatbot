from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import database and services
from app.db.database import init_db, get_db
from app.services.translation_service import TranslationDictionary
from app.services.ai_service import AIService

# Request/Response models
class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    question: str
    answer: str
    sql: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

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

# API Endpoints
@app.get("/")
def root():
    return {
        "message": "BI Chatbot API v2.0 - AI Powered", 
        "status": "active",
        "openai_key_configured": get_openai_key() != 'api-key'
    }

@app.post("/ask", response_model=QueryResponse)
async def ask_question_post(request: QueryRequest, db: Session = Depends(get_db)) -> QueryResponse:
    """Ask a question in natural language and get a response based on BI data with AI"""
    question = request.question
    
    try:
        print(f"📝 Received question: {question}")
        
        # Initialize AI service
        ai_service = AIService(db)
        
        # Step 1: Generate SQL from natural language question
        print("1. Generating SQL from question using AI...")
        sql_result = ai_service.generate_sql(question)
        
        if not sql_result.get('success'):
            return QueryResponse(
                question=question,
                answer=f"שגיאה ביצירת שאילתת SQL: {sql_result.get('error')}",
                error=sql_result.get('error')
            )
        
        sql_query = sql_result.get('sql')
        print(f"   Generated SQL: {sql_query}")
        
        # Step 2: Execute the query
        print("2. Executing SQL query...")
        query_results = ai_service.execute_query(sql_query)
        
        if not query_results.get('success'):
            return QueryResponse(
                question=question,
                answer=f"שגיאה בביצוע השאילתה: {query_results.get('error')}",
                sql=sql_query,
                error=query_results.get('error')
            )
        
        # Step 3: Generate natural language response
        print("3. Generating natural language response...")
        ai_answer = ai_service.generate_response(question, query_results, sql_query)
        
        return QueryResponse(
            question=question,
            answer=ai_answer,
            sql=sql_query,
            data=query_results.get('results', []),
            error=None
        )
        
    except Exception as e:
        error_msg = f"שגיאה בעיבוד השאלה: {str(e)}"
        print(f"❌ Error: {error_msg}")
        
        return QueryResponse(
            question=question,
            answer=error_msg,
            error=str(e)
        )

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",
        "openai_key": get_openai_key() != 'api-key'
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)