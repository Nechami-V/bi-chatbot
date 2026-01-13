**Project Shape**
- Monorepo with FastAPI backend in server/app and Vite React client in client/frontend-react.
- Shared contracts in server/shared/contracts.py keep request/response shapes synchronized.
- Config JSON assets live under server/config (not bundled client-side); adjust shared.settings paths if relocating.
- Data flow: question → NL2SQL → SQL execution → AI-written Hebrew answer plus optional visualization payload.

**Backend**
- FastAPI app in app/main.py duplicates routes at root and /api to keep legacy clients working under different API_BASE_URLs.
- services/executor/service.py uses SQLAlchemy text() with pyodbc; fetchmany(20) caps preview rows that reach the UI.
- shared/settings.py loads .env and raises immediately if OPENAI_API_KEY, DATABASE_URL, or CLIENT_ID are missing; set env before uvicorn.
- Chat routes in app/routes/chat.py wrap _handle_chat with timing metrics and Hebrew fallback messages for errors or SQL failures.

**NL2SQL Flow**
- services/nl2sql/service.py loads meta schema + semantic map, rewrites the question, sends OpenAI SQL_SYSTEM_PROMPT, and rejects non-SELECT responses.
- services/nl2sql/prompts.py encodes hard join rules (e.g. W_Orders.saleID → W_sales.id) and answer formatting instructions; update alongside schema changes.
- guardrails.validate_sql_against_semantic_rules enforces SELECT/WITH-only SQL and regex-based forbidden patterns prior to execution.
- semantic.py expects keys term writes/sql_hints/forbidden_patterns, while semantic_map.json currently exposes entities/forbidden; align data or extend loader before trusting hints.

**Frontend**
- src/App.tsx orchestrates chat history, analytics sidebar, and visualization derivation; most UX tweaks happen here.
- Visualization builder first consumes response.visualization, then falls back to buildVisualizationFromData using parseNumericValue helpers.
- API client in src/services/api.ts respects config.ts; API_BASE_URL defaults to window.origin and fetchWithTimeout manages tokens + timeouts.
- Auth toggled by DISABLE_AUTH (VITE_DISABLE_AUTH); UI still calls /auth endpoints so leave flag true unless backend implements them.

**Dev Workflow**
- Backend: cd server; pip install -r requirements.txt; run uvicorn app.main:app --reload (pyodbc SQL Server driver must be installed locally).
- Config: server/.env defines OPENAI_MODEL, DATABASE_URL, META_SCHEMA_PATH, SEMANTIC_MAP_PATH relative to the server working directory.
- Frontend: cd client/frontend-react; npm install; npm run dev or run_client.bat (installs then starts Vite dev server).
- Environment defaults: client .env sets VITE_API_BASE_URL and disables auth; keep it in sync with the server DISABLE_AUTH expectation.

**Caveats & Tips**
- execute_sql returns only preview rows (default 20) and row_count mirrors that preview; expand if exports need full result sets.
- ChatResponse strings are Hebrew; maintain localization when adding error messages or UI copy in either tier.
- No automated tests or lint scripts exist; manually verify NL2SQL changes against a live SQL Server and OpenAI account.
- SQL generation relies on server/config/meta_schema.json staying current; run load_meta_schema(force_reload=True) after updating the file to refresh cache.
