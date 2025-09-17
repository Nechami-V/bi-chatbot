from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.database import init_db, get_db
from app.services.translation_service import TranslationDictionary
from app.services.nlp_processor import NLPProcessor
from app.services.query_builder import QueryBuilder
from sqlalchemy.orm import Session

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

# Initialize services
dictionary = TranslationDictionary()
nlp_processor = NLPProcessor(dictionary)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    # This will create tables and add sample data
    init_db()

# Request/Response models
class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    question: str
    answer: str
    sql: Optional[str] = None
    error: Optional[str] = None

# API Endpoints
@app.get("/")
def root():
    return {
        "message": "BI Chatbot API is running",
        "endpoints": [
            {"path": "/ask", "method": "GET", "description": "Ask a question in natural language"},
            {"path": "/ask", "method": "POST", "description": "Ask a question in natural language (with JSON body)"}
        ]
    }

@app.get("/ask")
def ask_question(question: str, db: Session = Depends(get_db)) -> QueryResponse:
    """Ask a question in natural language and get a response based on BI data"""
    print("\n=== New Question ===")
    print(f"Question: {question}")
    try:
        # Process the question
        print("1. Processing question...")
        try:
            intent = nlp_processor.process_question(question)
            print(f"   Intent: {intent}")
        except Exception as e:
            print(f"Error processing question: {str(e)}")
            raise
        
        # Build and execute the query
        print("2. Building query...")
        try:
            query_builder = QueryBuilder(dictionary, db)
            query = query_builder.build_query(intent)
            print(f"   Query: {query}")
        except Exception as e:
            print(f"Error building query: {str(e)}")
            raise
        
        # Execute the query with the intent for better response formatting
        print("3. Executing query...")
        try:
            result = query_builder.execute_query(query, intent=intent)
            print(f"   Result: {result}")
            
            # If result is already a dictionary with the right format, use it
            if isinstance(result, dict) and 'answer' in result:
                return QueryResponse(
                    question=question,
                    answer=result.get('answer', 'No answer provided'),
                    sql=result.get('sql'),
                    error=result.get('error')
                )
            
            # Otherwise, format as a simple response
            return QueryResponse(
                question=question,
                answer=str(result) if result is not None else "No results found",
                sql=str(query) if hasattr(query, 'compile') else None,
                error=None
            )
        except Exception as e:
            print(f"Error executing query: {str(e)}")
            raise
            
        return QueryResponse(
            question=question,
            answer=result,
            sql=str(query) if hasattr(query, 'compile') else None,
            error=None
        )
        
    except Exception as e:
        return QueryResponse(
            question=question,
            answer=f"אירעה שגיאה בעיבוד השאלה: {str(e)}",
            error=str(e)
        )

@app.post("/ask", response_model=QueryResponse)
async def ask_question_post(request: QueryRequest, db: Session = Depends(get_db)) -> QueryResponse:
    """Ask a question in natural language (POST version with JSON body)"""
    return ask_question(request.question, db)
