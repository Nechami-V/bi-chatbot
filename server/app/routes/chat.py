import time
from fastapi import APIRouter, Request
from openai import OpenAI

from services.executor.service import execute_sql
from services.nl2sql.answer_ai import ai_format_answer
from services.nl2sql.service import generate_sql
from shared.contracts import ChatRequest, ChatResponse
from shared.settings import OPENAI_API_KEY, OPENAI_MODEL

router = APIRouter()
_answer_client = OpenAI(api_key=OPENAI_API_KEY)

STATE_CACHE = {}

def _cache_get(key: str):
    return STATE_CACHE.get(key)

def _cache_set(key: str, value):
    STATE_CACHE[key] = value

def _cache_del(key: str):
    STATE_CACHE.pop(key, None)

def _ctx_key(base: str) -> str:
    return f"{base}:ctx"

def _ctx_get(base: str) -> dict:
    return STATE_CACHE.get(_ctx_key(base), {}) or {}

def _ctx_set(base: str, ctx: dict):
    STATE_CACHE[_ctx_key(base)] = ctx

def _history_key(base: str) -> str:
    return f"{base}:history"

def _history_get(base: str) -> list:
    return STATE_CACHE.get(_history_key(base), [])

def _history_append(base: str, entry: dict, limit: int = 20):
    history = STATE_CACHE.get(_history_key(base), [])
    history.append(entry)
    STATE_CACHE[_history_key(base)] = history[-limit:]

def _needs_context(question: str) -> bool:
    q = question.strip()
    triggers = [
        "שם", "מזה", "כמו קודם", "אותו", "אותה", "שם זה",
        "איפה", "הכי הרבה", "הכי מעט"
    ]
    return any(t in q for t in triggers)

def _update_ctx_from_question(ctx: dict, question: str) -> dict:
    q = question.strip()

    if "בשבוע האחרון" in q or "שבוע אחרון" in q:
        ctx["last_time_window_days"] = 7
    if "בחודש האחרון" in q or "חודש אחרון" in q:
        ctx["last_time_window_days"] = 30

    for term in ["חלב", "לחם", "שמן"]:
        if term in q:
            ctx["last_item_term"] = term
            break

    return ctx

def _update_ctx_from_exec_result(ctx: dict, exec_res) -> dict:
    if not getattr(exec_res, "rows", None):
        return ctx
    row0 = exec_res.rows[0]
    if not isinstance(row0, dict):
        return ctx

    # עדכון תחנה רק משדה ייעודי (לא לנחש מ-"name")
    for key in ("station_name", "site_name"):
        val = row0.get(key)
        if isinstance(val, str) and val.strip():
            ctx["last_station_name"] = val.strip()
            break

    return ctx

def _ctx_to_text(ctx: dict) -> str:
    parts = []
    if ctx.get("last_item_term"):
        parts.append(f'last_item_term="{ctx["last_item_term"]}"')
    if ctx.get("last_time_window_days"):
        parts.append(f"last_time_window_days={ctx['last_time_window_days']}")
    if ctx.get("last_station_name"):
        parts.append(f'last_station_name="{ctx["last_station_name"]}"')
    if ctx.get("last_sql_excerpt"):
        parts.append(f'last_sql_excerpt="{ctx["last_sql_excerpt"]}"')
    return ", ".join(parts)

def _should_cache_response_id(new_id: str | None) -> bool:
    return bool(new_id and new_id.strip())

def _is_fallback_sql(sql: str) -> bool:
    s = (sql or "").lower()
    return "לא הצלחתי" in s or "לא ניתן" in s

def _handle_chat(req: ChatRequest, sid: str | None) -> ChatResponse:
    started = time.perf_counter()
    timings = {}
    sid = sid or "anonymous"
    base = f"session:{sid}:chat:main"

    key_sql = f"{base}:nl2sql"
    key_ans = f"{base}:answer"

    # ctx
    ctx = _ctx_get(base)
    ctx = _update_ctx_from_question(ctx, req.question)
    _ctx_set(base, ctx)

    prev_history = _history_get(base)
    sql_history_pairs = []
    answer_history_pairs = []
    for entry in prev_history[-10:]:
        question_text = (entry.get("question") or "").strip()
        sql_text = (entry.get("sql") or "").strip()
        answer_text = (entry.get("answer") or "").strip()
        error_text = (entry.get("error") or "").strip() if entry.get("error") else ""

        sql_parts = []
        if sql_text:
            sql_parts.append(f"SQL:\n{sql_text}")
        if answer_text:
            sql_parts.append(f"תשובה קודמת:\n{answer_text}")
        if error_text and not answer_text:
            sql_parts.append(f"שגיאה קודמת:\n{error_text}")
        sql_summary = "\n".join(sql_parts).strip()
        if question_text or sql_summary:
            sql_history_pairs.append((question_text, sql_summary))

        answer_summary = answer_text
        if error_text and not answer_summary:
            answer_summary = f"שגיאה קודמת: {error_text}"
        if question_text or answer_summary:
            answer_history_pairs.append((question_text, answer_summary))

    try:
        t0 = time.perf_counter()

        context_text = _ctx_to_text(ctx) if _needs_context(req.question) else ""
        last_sql_id = _cache_get(key_sql)

        nl2sql, new_sql_id = generate_sql(
            req.question,
            previous_response_id=last_sql_id,
            context_text=context_text,
            history=sql_history_pairs or None,
        )

        # לשמור response_id רק אם תקין ורק אם לא מדובר ב-fallback
        if _should_cache_response_id(new_sql_id) and not _is_fallback_sql(nl2sql.sql):
            _cache_set(key_sql, new_sql_id)

        timings["sql_gen"] = (time.perf_counter() - t0) * 1000

        if nl2sql.error:
            total_ms = (time.perf_counter() - started) * 1000
            timings["total"] = total_ms
            _history_append(base, {
                "question": req.question,
                "sql": nl2sql.sql,
                "answer": "לא ניתן היה להפיק שאילתה אמינה עבור השאלה.",
                "error": nl2sql.error,
                "timestamp": time.time(),
            })
            return ChatResponse(
                question=req.question,
                answer="לא ניתן היה להפיק שאילתה אמינה עבור השאלה.",
                sql=nl2sql.sql,
                data=[],
                columns=[],
                row_count=None,
                preview_count=0,
                has_more=False,
                error=nl2sql.error,
                total_time_ms=total_ms,
                timings_ms=timings,
            )

        ctx = _ctx_get(base)
        ctx["last_sql_excerpt"] = (nl2sql.sql[:500] if nl2sql.sql else "")
        _ctx_set(base, ctx)

        t1 = time.perf_counter()
        exec_res = execute_sql(nl2sql.sql)
        timings["db_exec"] = (time.perf_counter() - t1) * 1000

        ctx = _ctx_get(base)
        ctx = _update_ctx_from_exec_result(ctx, exec_res)
        _ctx_set(base, ctx)

        last_ans_id = _cache_get(key_ans)
        answer, new_ans_id = ai_format_answer(
            client=_answer_client,
            model=OPENAI_MODEL,
            question=req.question,
            row_count=exec_res.row_count,
            preview=exec_res.rows,
            error=exec_res.error,
            preview_count=exec_res.preview_count,
            has_more=exec_res.has_more,
            previous_response_id=last_ans_id,
            history=answer_history_pairs or None,

        )


        if _should_cache_response_id(new_ans_id):
            _cache_set(key_ans, new_ans_id)

        total_ms = (time.perf_counter() - started) * 1000
        timings["total"] = total_ms
        _history_append(base, {
            "question": req.question,
            "sql": nl2sql.sql,
            "answer": answer,
            "error": exec_res.error,
            "timestamp": time.time(),
        })

        return ChatResponse(
            question=req.question,
            answer=answer,
            sql=nl2sql.sql,
            data=exec_res.rows,
            columns=exec_res.columns,
            row_count=exec_res.row_count,
            preview_count=exec_res.preview_count,
            has_more=exec_res.has_more,
            error=exec_res.error,
            total_time_ms=total_ms,
            timings_ms=timings,
        )


    except Exception as exc:
        total_ms = (time.perf_counter() - started) * 1000
        timings["total"] = total_ms
        sql_text = None
        if "nl2sql" in locals() and getattr(nl2sql, "sql", None):
            sql_text = nl2sql.sql
        _history_append(base, {
            "question": req.question,
            "sql": sql_text,
            "answer": "קרתה שגיאה בזמן עיבוד השאלה.",
            "error": str(exc),
            "timestamp": time.time(),
        })
        return ChatResponse(
            question=req.question,
            answer="קרתה שגיאה בזמן עיבוד השאלה.",
            error=str(exc),
            total_time_ms=total_ms,
            timings_ms=timings,
        )

@router.post("/ask", response_model=ChatResponse)
def ask(request: Request, req: ChatRequest) -> ChatResponse:
    sid = request.cookies.get("sid")
    return _handle_chat(req, sid)

@router.post("/chat", response_model=ChatResponse)
def chat(request: Request, req: ChatRequest) -> ChatResponse:
    sid = request.cookies.get("sid")
    return _handle_chat(req, sid)

@router.post("/chat/reset")
def reset_chat(request: Request):
    sid = request.cookies.get("sid") or "anonymous"
    base = f"session:{sid}:chat:main"
    _cache_del(f"{base}:nl2sql")
    _cache_del(f"{base}:answer")
    _cache_del(f"{base}:ctx")
    _cache_del(_history_key(base))
    return {"ok": True}
