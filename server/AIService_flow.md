# AIService + ChatbotService End-to-End Flow

This document describes the full runtime flow for processing a user question inside the BI chatbot stack, including the key functions involved.

## 1. Service Initialization
1. `ChatbotService.__init__`
   - Receives a SQLAlchemy `Session` and optional `client_id`.
   - Creates an `AIService` instance with the same DB session and the configured system prompt from `app.simple_config.config`.
2. `AIService.__init__`
   - Stores the DB session, client id, and system prompt.
   - Calls `_analyze_database_schema()` to populate `self.schema_info`.
   - Imports `create_sql_generator` to prepare database-specific SQL translation helpers.
   - Confirms that `config.OPENAI_API_KEY` is defined and instantiates `OpenAI` client.

## 2. Schema Discovery Pipeline
1. `_analyze_database_schema`
   - Tries `_load_schema_from_meta_yaml` first.
   - Falls back to `_load_schema_from_yaml` if META schema is missing/empty.
   - Uses `_fallback_schema_analysis` as the last resort (direct DB introspection based on `config.BUSINESS_TABLES`).
2. `_load_schema_from_meta_yaml`
   - Calls `config_loader.load_meta_schema()` which parses `configs/schemas/META_SCHEMA.yaml`.
3. `_load_schema_from_yaml`
   - Uses `config_loader.load_shared_ontology()` and `load_client_config()` to merge ontology entities with client `datasource.yaml` mappings.
4. `_fallback_schema_analysis`
   - Uses `sqlalchemy.inspect` to pull table/column metadata for every table listed in `config.BUSINESS_TABLES`.

## 3. Request Handling Entry Point
1. `ChatbotService.process_question`
   - Normalizes the incoming text, builds a user id string, and captures timing checkpoints.
   - Retrieves conversation context from `session_memory.get_context_text(user_id)`.
   - If a prompt pack (`config.PACK`) is configured it tries `AIService.generate_pack_output`:
     - On success executes returned SQL with `_execute_query` and synthesizes an answer.
     - On failure or missing `sql_export` it falls back to the legacy flow.
   - Legacy flow steps:
     1. `_generate_sql` (delegates to `AIService.generate_sql`).
     2. `_execute_query` (delegates to `AIService.execute_query`).
     3. `_generate_response` (delegates to `AIService.generate_response`).
   - Persists the conversation turn via `session_memory.add_exchange` and returns a `QueryResponse`.

## 4. SQL Generation Deep Dive
1. `ChatbotService._generate_sql`
   - Calls `AIService.generate_sql(question, context_text)`.
2. `AIService.generate_sql`
   - Builds a prompt through `_build_sql_prompt` (injects schema snapshot, instructions, context).
   - Calls `_call_openai_for_sql` to obtain the raw model response.
   - Parses the output using `_parse_sql_response`:
     - Accepts JSON or extracts `SELECT` statements from free-form text.
     - Validates syntax via `validate_sql` (raising `SQLValidationError` on forbidden constructs).
   - Normalizes the SQL:
     - `_convert_limit_to_top` for MySQL-style `LIMIT` clauses.
     - `_apply_sql_fixes` for known patterns (e.g., `parents.week`).
     - `_ensure_select_statement` to wrap plain text responses into `SELECT '...'`.
   - Returns a dict with `success`, `sql`, `tables`, and timing metadata.
3. Helper functions in this stage:
   - `_select_relevant_tables`: serializes the schema into the prompt-friendly format.
   - `_get_reserved_columns`: flags columns that need `[brackets]` in SQL Server.
   - `_safe_json`, `_extract_json_block`, `_extract_select_sql`: resilient parsing utilities.

## 5. SQL Execution
1. `ChatbotService._execute_query`
   - Calls `AIService.execute_query(sql)`.
2. `AIService.execute_query`
   - Applies `_convert_limit_to_top` and `_ensure_select_statement` as last-resort guards.
   - Uses `self.sql_generator.translate_sql_functions` to swap cross-database functions if needed.
   - Executes the query with SQLAlchemy `text(sql)`.
   - Returns `{success, results, row_count, duration_sec}` for `SELECT` statements; commits and reports rows affected for DML.
   - Rolls back and returns an error payload on exceptions.

## 6. Natural-Language Answer Generation
1. `ChatbotService._generate_response`
   - Calls `AIService.generate_response(question, query_results, context_text)`.
2. `AIService.generate_response`
   - Crafts a short Hebrew instruction prompt with sample row data.
   - Calls OpenAI chat completion with the configured model and max tokens (capped at 160).
   - Detects generic/empty responses and performs a second stricter pass if required.
   - Uses `_format_explicit_answer` as deterministic fallback when the model is unavailable or blocked.
   - Final result is always a single Hebrew sentence; default messages are used when the dataset is empty.

## 7. Conversation Memory
- `session_memory` (from `app.simple_memory`) stores full chat transcripts keyed by user id.
- `ChatbotService.process_question` reads existing context and appends each exchange.
- A manual reset is available through `session_memory.reset_session(user_id)`.

## 8. Prompt Pack Path (Optional)
1. `ChatbotService.process_question`
   - Triggered when `config.PACK` is non-empty.
2. `AIService.generate_pack_output`
   - Lazily initializes `PromptManager`.
   - Renders templates (`answer`, `sql_export`, `sql_ratio`) with schema + context variables.
   - Calls `_call_openai_chat` for each template, expecting JSON payloads with specific keys.
3. Successful pack output:
   - Uses returned `sql_export` to query the DB, falls back to `generate_response` if `short_answer` is empty.

## 9. Error Handling and Logging
- Errors in SQL generation or execution bubble to `_error_response` in `ChatbotService`, which returns Hebrew error text inside `QueryResponse`.
- Schema-loading issues cascade gracefully between META YAML → ontology YAML → DB introspection.
- Extensive logging uses `logger.info` / `logger.warning` / `logger.error` for tracing.

---
This flow captures the complete call graph from API request to SQL execution and response generation, referencing the primary functions involved at each stage.
