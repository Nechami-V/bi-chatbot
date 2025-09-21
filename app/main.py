from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

# Import from our new structure
from app.db.database import init_db, get_db
from app import TranslationDictionary, NLPProcessor, QueryBuilder

# Request/Response models
class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    question: str
    answer: str
    sql: Optional[str] = None
    error: Optional[str] = None

# Initialize shared services
_dictionary = TranslationDictionary()
_nlp = NLPProcessor(_dictionary)

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

@app.get("/ask", response_model=QueryResponse)
def ask_question_get(question: str, db: Session = Depends(get_db)) -> QueryResponse:
    """Ask a question in natural language and get a response based on BI data (GET)."""
    try:
        intent = _nlp.process_question(question)
        query_builder = QueryBuilder(_dictionary, db)
        query = query_builder.build_query(intent)
        result = query_builder.execute_query(query, intent=intent)

        if isinstance(result, dict) and 'answer' in result:
            return QueryResponse(
                question=question,
                answer=result.get('answer', 'No answer provided'),
                sql=result.get('sql'),
                error=result.get('error')
            )

        return QueryResponse(
            question=question,
            answer=str(result) if result is not None else "No results found",
            sql=str(query),
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
    """Ask a question in natural language (POST) with JSON body."""
    return ask_question_get(request.question, db)
