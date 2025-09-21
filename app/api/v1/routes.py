from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import get_db
from app import QueryRequest, QueryResponse
from app import TranslationDictionary
from app import NLPProcessor
from app import QueryBuilder

router = APIRouter()

# Initialize shared services for this router
_dictionary = TranslationDictionary()
_nlp = NLPProcessor(_dictionary)


@router.get("/ask", response_model=QueryResponse)
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


@router.post("/ask", response_model=QueryResponse)
async def ask_question_post(request: QueryRequest, db: Session = Depends(get_db)) -> QueryResponse:
    """Ask a question in natural language (POST) with JSON body."""
    return ask_question_get(request.question, db)
