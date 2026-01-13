"""Helpers for turning result sets into natural-language answers."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from services.nl2sql.prompts import ANSWER_SYSTEM_PROMPT, format_conversation_history

answer_prompt = ANSWER_SYSTEM_PROMPT


def _shrink_preview(preview: List[Dict[str, Any]], max_rows: int = 20) -> List[Dict[str, Any]]:
    return preview[:max_rows] if preview else []


def build_answer_payload(
    question: str,
    row_count: Optional[int],
    preview: List[Dict[str, Any]],
    error: Optional[str] = None,
    preview_count: Optional[int] = None,
    has_more: Optional[bool] = None,
) -> Dict[str, Any]:
    safe_preview = [] if error else _shrink_preview(preview, max_rows=20)

    if preview_count is None:
        preview_count = len(safe_preview)

    return {
        "question": question,
        "row_count": row_count,
        "preview": safe_preview,          # ✅ להשתמש ב-safe_preview
        "error": error,
        "preview_count": preview_count,
        "has_more": has_more,
    }


def ai_format_answer(
    client,
    model: str,
    question: str,
    row_count: Optional[int],
    preview: List[Dict[str, Any]],
    error: Optional[str] = None,
    preview_count: Optional[int] = None,
    has_more: Optional[bool] = None,
    previous_response_id: Optional[str] = None,
    history: Optional[List[Tuple[str, str]]] = None,
) -> Tuple[str, str]:
    print(f"  [ANSWER_AI] Formatting answer for {len(preview)} rows...")

    payload = build_answer_payload(
        question=question,
        row_count=row_count,
        preview=preview,
        error=error,
        preview_count=preview_count,
        has_more=has_more,
    )

    history_text = format_conversation_history(history)

    user_sections = []
    if history_text:
        user_sections.append(history_text)
    user_sections.append(
        "Here is the query result data in JSON format. "
        "Please generate a user-friendly answer:\n"
        + json.dumps(payload, ensure_ascii=False)
    )
    user_msg = "\n\n".join(user_sections)

    # ✅ לא לשרשר תשובה אם אין נתונים/יש שגיאה
    chain_id = previous_response_id
    if error or (row_count is not None and row_count <= 0):
        chain_id = None

    response_id = chain_id or ""

    try:
        if hasattr(client, "responses"):
            input_messages = [{"role": "user", "content": user_msg}]
            resp = client.responses.create(
                model=model,
                instructions=answer_prompt,
                previous_response_id=chain_id,
                input=input_messages,
            )
            answer = (resp.output_text or "").strip()
            response_id = resp.id
        else:
            raise AttributeError("responses API not available")
    except Exception:
        fallback_messages = [
            {"role": "system", "content": answer_prompt},
            {"role": "user", "content": user_msg},
        ]
        resp = client.chat.completions.create(
            model=model,
            messages=fallback_messages,
            temperature=0,
        )
        answer = (resp.choices[0].message.content or "").strip()
        response_id = getattr(resp, "id", response_id)
    print(f"  [ANSWER_AI] Answer generated.")
    return answer, response_id
