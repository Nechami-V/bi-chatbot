from openai import OpenAI
from shared.settings import OPENAI_API_KEY, OPENAI_MODEL
from shared.contracts import NL2SQLResponse
from .prompts import SQL_SYSTEM_PROMPT, build_user_prompt
from .meta_schema import load_meta_schema, build_prompt_schema_text
from services.nl2sql.semantic import apply_semantic_mapping, load_semantic_map
from services.nl2sql.guardrails import validate_sql_against_semantic_rules

_client = OpenAI(api_key=OPENAI_API_KEY)

def generate_sql(
    question: str,
    previous_response_id: str | None = None,
    context_text: str = "",
    history: list[tuple[str, str]] | None = None,
) -> tuple[NL2SQLResponse, str]:
    print(f"  [NL2SQL] Generating SQL for: {question}")

    meta = load_meta_schema()
    if meta.warnings:
        print("META SCHEMA WARNINGS:")
        for w in meta.warnings[:50]:
            print(" -", w)

    schema_text = build_prompt_schema_text(meta)
    semantic = load_semantic_map()

    original_question = question
    mapped_question, semantic_rules_text = apply_semantic_mapping(original_question, semantic)

    system_prompt = SQL_SYSTEM_PROMPT + "\n\n" + semantic_rules_text

    # חשוב: לשלוח למודל את השאלה הממופה (כדי שימצא טבלאות/שדות נכון)
    user_prompt = build_user_prompt(
        mapped_question,
        schema_text,
        context_text,
        conversation_history=history,
    )

    def _call(previous_id: str | None):
        if not hasattr(_client, "responses"):
            return None
        input_messages = [{"role": "user", "content": user_prompt}]
        return _client.responses.create(
            model=OPENAI_MODEL,
            instructions=system_prompt,
            previous_response_id=previous_id,
            input=input_messages,
        )

    try:
        resp = None
        if hasattr(_client, "responses"):
            resp = _call(previous_response_id)
        if not resp:
            raise ValueError("Responses API unavailable")
    except Exception as e1:
        # fallback: אם נכשל בגלל previous_response_id / state - ננסה בלי המשכיות
        try:
            if hasattr(_client, "responses"):
                resp = _call(None)
            else:
                raise ValueError("Responses API unavailable")
        except Exception as e2:
            try:
                fallback_messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
                resp = _client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=fallback_messages,
                    temperature=0,
                )
            except Exception as e3:
                return (
                    NL2SQLResponse(
                        sql="SELECT N'לא ניתן לייצר SQL כרגע' AS message;",
                        error=str(e3),
                    ),
                    previous_response_id or "",
                )

    if hasattr(resp, "output_text"):
        sql = (resp.output_text or "").strip()
        response_id = resp.id
    else:
        sql = (resp.choices[0].message.content or "").strip()
        response_id = previous_response_id or ""

    idx = sql.lower().find("select")
    if idx != -1:
        sql = sql[idx:].strip()
    else:
        sql = "SELECT N'לא הצלחתי לייצר שאילתה תקינה' AS message;"

    if not sql.lower().lstrip().startswith("select"):
        sql = "SELECT N'לא הצלחתי לייצר שאילתה תקינה' AS message;"

    print(f"  [NL2SQL] Raw SQL: {sql}")

    try:
        validate_sql_against_semantic_rules(sql, semantic)
    except ValueError as e:
        return (
            NL2SQLResponse(
                sql="SELECT N'לא ניתן לייצר SQL אמין לשאלה זו לפי חוקי הסכימה' AS message;",
                error=str(e),
            ),
            response_id,
        )

    return NL2SQLResponse(sql=sql), response_id
