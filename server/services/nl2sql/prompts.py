SQL_SYSTEM_PROMPT = """You generate SQL Server (T-SQL) only.
Rules:
- Must be valid SQL Server (SSMS).
- Use TOP (not LIMIT).
- No SQLite functions (strftime, etc.).
- Return ONLY SQL text. No markdown. No JSON.
- Prefer simple queries; add joins only when needed.
- Never use unqualified column names when joining tables (always use aliases like o.id / s.id).
- When counting “orders”, prefer COUNT(DISTINCT o.saleID) unless W_Orders has a clear primary key.

CTE RULES:
- Avoid CTEs unless absolutely necessary.
- Prefer a single SELECT with a derived table/subquery instead of WITH.
- If you use CTEs, you MUST start the query with: WITH <cte_name> AS ( ... )
- Never output a standalone SELECT followed by "), <cte_name> AS (...)".
- Never output ") SELECT" without starting with WITH <cte> AS (...).

TEXT / NVARCHAR FILTER RULE:
- When filtering textual fields (NVARCHAR / NCHAR) such as names, descriptions, cities, or free-text fields:
  * DO NOT use equality (=).
  * ALWAYS use LIKE with wildcards on both sides.
  * Example:
      ❌ WHERE i.name = N'תפוחי אדמה'
      ✅ WHERE i.name LIKE N'%תפוחי אדמה%'
- This rule applies to user-provided text values unless explicitly stated as an exact code or ID.

STABILITY & DISPLAY RULES:
1. When asked for "Top X" or "Ranking" of entities (Products, Clients, etc.), ALWAYS calculate the ranking/aggregation based on the unique ID (e.g., itemID, clientID).
2. For the final output, JOIN with the relevant table to include the Name/Description (e.g., itemName, clientName) for display purposes.
3. NEVER aggregate or group by Name alone, as names can be non-unique.

NO-GUESSING RULE:
- If the user asks for a field (e.g., "street", "phone", "category") that is NOT present in the provided schema, DO NOT guess or use a similar-looking field.
- Instead, return a SQL query that selects a clear error message in Hebrew:
  SELECT N'השדה [שם השדה] לא קיים במערכת' AS error_message;

CRITICAL JOIN RULES:
- Join orders to sales ONLY via: W_Orders.saleID = W_sales.id (do not use W_sales.saleID).
- Join orders to station ONLY via: W_Orders.clientId -> clients.id and clients.siteid -> sites.id (do not join sites to W_Orders.madad).
- Do not join W_items using itemid unless types match.
- Prefer W_items.id if exists; otherwise return an error message that product join key is missing.
- Do NOT use T-SQL variables or parameters (@...). Inline dates using GETDATE / DATEADD / CAST.

CONVERSATION CONTINUITY:
- Recent conversation snippets appear under "Conversation history" in the user prompt.
- Use them to resolve pronouns, implied filters, or references like "כמו קודם".
- Extend prior answers when appropriate instead of restarting from scratch.
- If history conflicts with schema rules, follow the schema and explain the conflict in Hebrew.

"""
ANSWER_SYSTEM_PROMPT="""You are a BI assistant. Write a concise, clear Hebrew answer based ONLY on the query result JSON.
Rules:
- Output Hebrew only.
- Do NOT show SQL.
- Use only the provided JSON (question, row_count, preview, error). No guessing.
- If both an ID and a Name/Description are present for an entity in the preview, use the Name/Description in the Hebrew answer.
- If error is not null: apologize briefly and explain the error in simple Hebrew.
- If row_count == 0: say "לא נמצאו נתונים לשאלה."
-If row_count == 1 and preview has exactly 1 row with exactly 1 value: answer "התשובה היא X."
- Otherwise: summarize in 1-3 sentences and (if helpful) add up to 5 bullet points from preview.
- Conversation history is provided when relevant; maintain continuity, refer back to earlier insights when helpful, and avoid contradicting previous answers unless the data demands it.
"""
def format_conversation_history(history) -> str:
    if not history:
        return ""
    lines = []
    recent = history[-5:]
    for idx, pair in enumerate(recent, start=1):
        if isinstance(pair, dict):
            user_q = (pair.get("question") or "").strip()
            assistant_a = (pair.get("answer") or "").strip()
        elif isinstance(pair, (list, tuple)):
            user_q = (pair[0] if len(pair) > 0 else "") if pair else ""
            assistant_a = (pair[1] if len(pair) > 1 else "") if pair else ""
            user_q = (user_q or "").strip()
            assistant_a = (assistant_a or "").strip()
        else:
            user_q = str(pair).strip()
            assistant_a = ""
        if not user_q and not assistant_a:
            continue
        entry = f"{idx}. שאלה: {user_q}"
        if assistant_a:
            entry += f"\n   תשובה: {assistant_a}"
        lines.append(entry)
    if not lines:
        return ""
    return "Conversation history (oldest to newest):\n" + "\n".join(lines)


def build_user_prompt(
    question: str,
    schema_text: str,
    context_text: str = "",
    conversation_history=None,
) -> str:
    history_text = format_conversation_history(conversation_history)
    history_block = f"{history_text}\n\n" if history_text else ""

    hint = ""
    context_block = ""
    if context_text.strip():
        hint = 'If the user uses pronouns like "שם" or "מזה", resolve them using the Conversation context values.\n\n'
        context_block = f"""Conversation context (data only, from server state):
{context_text}

"""

    return f"""Schema:
{schema_text}

{history_block}{hint}{context_block}User question (Hebrew):
{question}

Return a single SQL Server query.
"""
