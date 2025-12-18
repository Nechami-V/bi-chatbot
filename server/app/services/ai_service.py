"""
AI Service - Natural Language Processing for Business Intelligence

This service provides AI-powered natural language understanding for converting
Hebrew business questions into SQL queries and generating intelligent responses.

Key Features:
- OpenAI GPT integration for natural language processing
- Database schema analysis and understanding
- Hebrew language support for business terms
- SQL query generation and validation
- Natural language response generation
- Measures execution time for each operation

Author: BI Chatbot Team
Version: 2.1.0
"""

import json
import logging
import re
import time
from typing import Dict, Optional, Any, List, Set, Tuple

from openai import OpenAI
from sqlalchemy.orm import Session
from sqlalchemy import inspect, text

from app.simple_config import config
from app.config_loader import ConfigurationError, config_loader
from app.services.prompt_manager import PromptManager, PromptNotConfigured
from app.services.sql_validator import SQLValidationError, validate_sql

# Configure logger
logger = logging.getLogger(__name__)

# Common SQL Server reserved keywords that require bracket quoting when used as identifiers
SQLSERVER_RESERVED_KEYWORDS: Set[str] = {
    "ADD",
    "ALL",
    "ALTER",
    "AND",
    "ANY",
    "AS",
    "ASC",
    "AUTHORIZATION",
    "BACKUP",
    "BEGIN",
    "BETWEEN",
    "BREAK",
    "BROWSE",
    "BULK",
    "BY",
    "CASCADE",
    "CASE",
    "CHECK",
    "CHECKPOINT",
    "CLOSE",
    "CLUSTERED",
    "COALESCE",
    "COLUMN",
    "COMMIT",
    "COMPUTE",
    "CONSTRAINT",
    "CONTAINS",
    "CONTINUE",
    "CONVERT",
    "CREATE",
    "CROSS",
    "CURRENT",
    "CURRENT_DATE",
    "CURRENT_TIME",
    "CURRENT_TIMESTAMP",
    "CURRENT_USER",
    "CURSOR",
    "DATABASE",
    "DBCC",
    "DEALLOCATE",
    "DECLARE",
    "DEFAULT",
    "DELETE",
    "DENY",
    "DESC",
    "DISK",
    "DISTINCT",
    "DISTRIBUTED",
    "DOUBLE",
    "DROP",
    "ELSE",
    "END",
    "ERRLVL",
    "ESCAPE",
    "EXCEPT",
    "EXEC",
    "EXECUTE",
    "EXISTS",
    "EXIT",
    "EXTERNAL",
    "FETCH",
    "FILE",
    "FILLFACTOR",
    "FOR",
    "FOREIGN",
    "FREETEXT",
    "FROM",
    "FULL",
    "FUNCTION",
    "GOTO",
    "GRANT",
    "GROUP",
    "HAVING",
    "HOLDLOCK",
    "IDENTITY",
    "IDENTITY_INSERT",
    "IDENTITYCOL",
    "IF",
    "IN",
    "INDEX",
    "INNER",
    "INSERT",
    "INTERSECT",
    "INTO",
    "IS",
    "JOIN",
    "KEY",
    "KILL",
    "LEFT",
    "LIKE",
    "LINENO",
    "LOAD",
    "MERGE",
    "NATIONAL",
    "NOCHECK",
    "NONCLUSTERED",
    "NOT",
    "NULL",
    "NULLIF",
    "OF",
    "OFF",
    "OFFSETS",
    "ON",
    "OPEN",
    "OPENDATASOURCE",
    "OPENQUERY",
    "OPENROWSET",
    "OPENXML",
    "OPTION",
    "OR",
    "ORDER",
    "OUTER",
    "OVER",
    "PERCENT",
    "PIVOT",
    "PLAN",
    "PRECISION",
    "PRIMARY",
    "PRINT",
    "PROC",
    "PROCEDURE",
    "PUBLIC",
    "RAISERROR",
    "READ",
    "READTEXT",
    "RECONFIGURE",
    "REFERENCES",
    "REPLICATION",
    "RESTORE",
    "RESTRICT",
    "RETURN",
    "REVERT",
    "REVOKE",
    "RIGHT",
    "ROLLBACK",
    "ROWCOUNT",
    "ROWGUIDCOL",
    "RULE",
    "SAVE",
    "SCHEMA",
    "SECURITYAUDIT",
    "SELECT",
    "SEMANTICKEYPHRASETABLE",
    "SEMANTICSIMILARITYDETAILSTABLE",
    "SEMANTICSIMILARITYTABLE",
    "SESSION_USER",
    "SET",
    "SETUSER",
    "SHUTDOWN",
    "SOME",
    "STATISTICS",
    "SYSTEM_USER",
    "TABLE",
    "TABLESAMPLE",
    "TEXTSIZE",
    "THEN",
    "TO",
    "TOP",
    "TRAN",
    "TRANSACTION",
    "TRIGGER",
    "TRUNCATE",
    "TRY_CONVERT",
    "TSEQUAL",
    "UNION",
    "UNIQUE",
    "UNPIVOT",
    "UPDATE",
    "UPDATETEXT",
    "USE",
    "USER",
    "VALUES",
    "VARYING",
    "VIEW",
    "WAITFOR",
    "WHEN",
    "WHERE",
    "WHILE",
    "WITH",
    "WITHIN",
    "WRITETEXT",
}


class AIService:
    """
    AI Service for Natural Language to SQL Processing
    
    This service handles all AI-related operations for the BI Chatbot system,
    enabling users to ask business questions in Hebrew and receive intelligent
    answers based on database analysis.
    """

    def __init__(self, db: Session, system_prompt: Optional[str] = None, client_id: str = "KT"):
        self.db = db
        self.client_id = client_id
        self.system_prompt = system_prompt or (
            "You are a helpful BI assistant that converts Hebrew business questions into SQL and answers clearly."
        )
        self.schema_info = self._analyze_database_schema()
        # Prompt manager is optional for legacy flows; initialize lazily when PACK is set
        self._prompt_mgr: Optional[PromptManager] = None
        
        # Import and create SQL generator for translation
        from app.query_ast.sql_generator import create_sql_generator
        self.sql_generator = create_sql_generator(client_id)

        if not config.OPENAI_API_KEY:
            raise ValueError("OpenAI API key is not configured. Please set OPENAI_API_KEY.")

        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        logger.info("AI Service initialized successfully")

    def _analyze_database_schema(self) -> Dict[str, Any]:
        schema = self._load_schema_from_meta_yaml()
        if schema.get("tables"):
            logger.info(
                "Schema source: META_SCHEMA.yaml (%d tables)",
                len(schema["tables"]),
            )
            return schema

        logger.warning("META_SCHEMA.yaml missing or empty; loading legacy YAML configuration")
        schema = self._load_schema_from_yaml()
        if schema.get("tables"):
            logger.info(
                "Schema source: legacy YAML (%d tables)",
                len(schema["tables"]),
            )
        return schema

    def _load_schema_from_meta_yaml(self) -> Dict[str, Any]:
        try:
            schema = config_loader.load_meta_schema()
            if schema.get("tables"):
                logger.info(
                    "Loaded schema from META_SCHEMA.yaml (%d tables)",
                    len(schema["tables"]),
                )
            else:
                logger.warning("META_SCHEMA.yaml found but contains no tables")
            return schema
        except ConfigurationError as exc:
            logger.warning("META_SCHEMA.yaml not available: %s", exc)
        except Exception:
            logger.exception("Failed to load META_SCHEMA.yaml")
        return {}

    def _load_schema_from_yaml(self) -> Dict[str, Any]:
        """Load schema from legacy client YAML configuration as final fallback."""
        logger.info(f"Loading database schema from YAML configuration for client: {self.client_id}...")

        try:
            ontology = config_loader.load_shared_ontology()
            datasource, _ = config_loader.load_client_config(self.client_id)

            schema = {"tables": {}, "relationships": []}

            for entity_name, entity in ontology.entities.items():
                if entity_name not in datasource.table_mappings:
                    continue

                table_mapping = datasource.table_mappings[entity_name]
                physical_table = table_mapping.physical_table

                columns = []
                primary_keys = []

                for attr_name, attribute in entity.attributes.items():
                    if attr_name not in table_mapping.columns:
                        continue

                    physical_col = table_mapping.columns[attr_name]

                    columns.append(
                        {
                            "name": physical_col,
                            "logical_name": attr_name,
                            "type": attribute.type.value,
                            "nullable": attribute.nullable,
                            "hebrew_names": attribute.hebrew_names,
                            "primary_key": attribute.primary_key,
                        }
                    )

                    if attribute.primary_key:
                        primary_keys.append(physical_col)

                schema["tables"][physical_table] = {
                    "entity_name": entity_name,
                    "display_name": entity.display_name,
                    "hebrew_names": entity.hebrew_names,
                    "columns": columns,
                    "primary_key": primary_keys,
                    "foreign_keys": [],
                }

            if ontology.relationships:
                for _, relationship in ontology.relationships.items():
                    schema["relationships"].append(
                        {
                            "from_entity": relationship.from_entity,
                            "to_entity": relationship.to_entity,
                            "type": relationship.type.value,
                            "foreign_key": relationship.foreign_key,
                        }
                    )

            logger.info(f"Loaded schema for {len(schema['tables'])} tables from YAML")
            return schema

        except Exception as exc:
            logger.error(f"Failed to load schema from YAML: {exc}")
            return self._fallback_schema_analysis()
    
    def _fallback_schema_analysis(self) -> Dict[str, Any]:
        """Fallback to original database introspection if YAML fails"""
        logger.info("Using fallback database schema analysis...")
        inspector = inspect(self.db.get_bind())
        schema = {"tables": {}, "relationships": []}
        relevant_tables = config.BUSINESS_TABLES if hasattr(config, 'BUSINESS_TABLES') else []

        for table_name in relevant_tables:
            if table_name not in inspector.get_table_names():
                logger.warning(f"Table {table_name} not found in database")
                continue

            columns = [
                {
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col["nullable"],
                    "default": col.get("default"),
                    "primary_key": col.get("primary_key", False),
                }
                for col in inspector.get_columns(table_name)
            ]

            primary_keys = [c["name"] for c in columns if c.get("primary_key", False)]
            
            schema["tables"][table_name] = {
                "columns": columns,
                "primary_key": primary_keys,
                "foreign_keys": [],
            }

        return schema

    def generate_sql(self, question: str, context_text: str = "") -> Dict[str, Any]:
        """
        Generate SQL query from natural language question.
        
        Args:
            question: User's question in Hebrew
            context_text: Optional context text to add to prompt
            
        Returns:
            Dict with success, sql, and optional error
        """
        start_time = time.perf_counter()

        prompt = self._build_sql_prompt(question, context_text)
        last_raw = None
        try:
            t0 = time.perf_counter()
            response = self._call_openai_for_sql(prompt)
            elapsed = time.perf_counter() - t0
            logger.info(f"SQL generation via OpenAI took {elapsed:.2f} seconds")
            last_raw = response

            parsed = self._parse_sql_response(response)
            if parsed.get("success") and (parsed.get("sql") or "").strip():
                sql = parsed.get("sql", "")
                
                # Final safety check for LIMIT before returning
                if "LIMIT" in sql.upper():
                    logger.warning("⚠️ FINAL CHECK: Found LIMIT in generated SQL - converting to TOP")
                    sql = self._convert_limit_to_top(sql)
                    parsed["sql"] = sql

                # Apply additional SQL hygiene fixes
                sql = self._apply_sql_fixes(sql)
                sql = self._ensure_select_statement(sql)
                parsed["sql"] = sql
                
                total = time.perf_counter() - start_time
                parsed["duration_sec"] = total
                logger.info(f"✅ Full SQL generation succeeded in {total:.2f} seconds")
                logger.info(f"Final SQL: {sql}")
                return parsed

            error = parsed.get("error") or "Empty SQL after parse"
        except Exception as e:
            error = str(e)

        total = time.perf_counter() - start_time
        logger.error(f"❌ SQL generation failed after {total:.2f} seconds. Error: {error}")
        return {
            "success": False,
            "error": error or "SQL generation returned empty result",
            "sql": "",
            "tables": [],
            "description": "",
            "raw_response": last_raw,
            "duration_sec": total,
        }

    # New: unified prompt-pack flow producing a single JSON with short_answer/sql_export/sql_ratio
    def generate_pack_output(self, question: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Use prompt packs to produce a single JSON with the three outputs.

        This calls the model once per type and merges the JSON fields to a single object.
        If PACK is not configured, raises clearly.
        """
        if not config.PACK:
            raise PromptNotConfigured("PACK is not set; cannot use prompt packs")

        if self._prompt_mgr is None:
            self._prompt_mgr = PromptManager()

        outputs: Dict[str, Any] = {}
        errors: Dict[str, str] = {}

        # Minimal context for templates
        ctx = dict(variables or {})
        ctx.setdefault("question", question)

        for t in ("answer", "sql_export", "sql_ratio"):
            try:
                prompt = self._prompt_mgr.render(t, schema=self.schema_info, variables=ctx)
                # Call OpenAI
                resp = self._call_openai_chat(prompt)
                obj = self._safe_json(resp)
                if not isinstance(obj, dict):
                    raise ValueError("Model did not return a JSON object")
                # Extract expected field
                key_map = {
                    "answer": "short_answer",
                    "sql_export": "sql_export",
                    "sql_ratio": "sql_ratio",
                }
                key = key_map[t]
                val = obj.get(key)
                if not val:
                    raise ValueError(f"Missing '{key}' in model output")
                outputs[key] = val
            except Exception as e:
                errors[t] = str(e)

        if errors:
            logger.warning(f"Prompt pack generation had errors: {errors}")

        return outputs

    # Internal helpers for prompt-pack calls
    def _call_openai_chat(self, prompt: str) -> str:
        completion = self.client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[{"role": "developer", "content": self.system_prompt}, {"role": "user", "content": prompt}],
            temperature=config.TEMPERATURE,
        )
        return completion.choices[0].message.content or ""

    def _safe_json(self, s: str) -> Any:
        try:
            return json.loads(s)
        except Exception:
            # Try to extract a JSON object from text
            m = re.search(r"\{[\s\S]*\}", s)
            if m:
                try:
                    return json.loads(m.group(0))
                except Exception:
                    pass
        return {}
    def _build_sql_prompt(self, question: str, context_text: str = "") -> str:
        """
        Build SQL generation prompt.
        
        Args:
            question: User's question in Hebrew
            context_text: Optional conversation context to add
            
        Returns:
            Formatted prompt string
        """
        # Detect database type from config
        from app.config_loader import config_loader
        try:
            datasource, _ = config_loader.load_client_config(self.client_id)
            db_type = datasource.database_type.value
            if db_type == "sqlserver" or db_type == "mssql":
                db = "SQL Server"
            else:
                # Force SQL Server - this system only supports T-SQL
                logger.warning(f"Unsupported database type: {db_type}. Forcing SQL Server.")
                db = "SQL Server"
        except:
            db = "SQL Server"  # Default to SQL Server
            
        tables_summary = self._select_relevant_tables(question)
        schema_brief = json.dumps({"tables": tables_summary}, ensure_ascii=False)
        
        # Extract table names for reference
        table_names = list(self.schema_info.get("tables", {}).keys())

        reserved_columns = self._get_reserved_columns()
        if reserved_columns:
            reserved_instruction = (
                "10. Wrap column names that are SQL Server reserved keywords in square brackets.\n"
                f"   Columns requiring brackets: {', '.join(f'[{col}]' for col in reserved_columns)}\n"
                "   Example: SELECT sl.[begin] FROM ...\n"
            )
        else:
            reserved_instruction = ""
        
        # ONLY SQL Server T-SQL syntax - NO SQLite/MySQL/PostgreSQL
        date_examples = (
            "3. For week: DATEPART(week, time)\n"
            "4. For year: YEAR(time)\n"
            "5. Current date: GETDATE()\n"
            "6. Previous year: YEAR(DATEADD(year, -1, GETDATE()))\n"
            "7. Date range: WHERE time >= DATEADD(day, -7, GETDATE())\n\n"
        )
        example_queries = (
            "EXAMPLES SQL Server T-SQL:\n"
            "SELECT COUNT(*) FROM Orders WHERE YEAR(time) = YEAR(GETDATE())\n"
            "SELECT DATEPART(week, time) as week_num, COUNT(*) FROM Orders GROUP BY DATEPART(week, time)\n"
            "SELECT COUNT(*) FROM Orders WHERE YEAR(time) = YEAR(DATEADD(year, -1, GETDATE()))\n\n"
        )
        forbidden_functions = (
            "FORBIDDEN - NEVER USE:\n"
            "- SQLite: strftime(), date('now')\n"
            "- PostgreSQL: DATE_TRUNC(), INTERVAL, CURRENT_DATE\n"
            "- MySQL: CURDATE(), NOW(), DATE_SUB(), DATE_ADD()\n\n"
        )
        allowed_functions = (
            "USE ONLY SQL SERVER T-SQL:\n"
            "- GETDATE(), YEAR(), MONTH(), DAY(), DATEPART()\n"
            "- DATEADD(day/week/month/year, number, date)\n"
            "- CAST(GETDATE() AS DATE)\n"
            "- DATEDIFF(day, start_date, end_date)\n\n"
        )
        
        base_prompt = (
            f"Create a SQL SELECT query for SQL Server (T-SQL) from this Hebrew business question.\n\n"
            "🔴 CRITICAL SQL SERVER SYNTAX REQUIREMENTS:\n"
            "1. Use TOP N at the start of SELECT - NEVER use LIMIT\n"
            "   - CORRECT: SELECT TOP 10 * FROM ...\n"
            "   - WRONG: SELECT * FROM ... LIMIT 10\n"
            "2. Use ONLY these EXACT table and column names:\n"
            f"   Available tables: {', '.join(table_names)}\n\n"
            "📋 SCHEMA WITH CORRECT NAMES:\n"
            f"{schema_brief}\n\n"
            "✅ INSTRUCTIONS:\n"
            "1. Use ONLY 'physical_name' values from the schema above\n"
            "2. Match Hebrew words to 'hebrew_names' to understand what the user wants\n"
            f"{date_examples}"
            "6. When using table aliases, avoid SQL reserved keywords (IS, AS, ON, IN, OR, AND, NOT, etc.)\n"
            "   - GOOD aliases: itm, itmsl, ord, lst, cli, c, l, o\n"
            "   - BAD aliases: IS, AS, ON, IN (these are reserved keywords)\n"
            "7. Performance: Always add WHERE filters BEFORE joins when possible\n"
            "8. When counting units/quantities, use SUM(units) not COUNT(*)\n"
            "9. For limiting results: SELECT TOP N ... (place TOP immediately after SELECT)\n\n"
            "10. If the question is a generic greeting (e.g. שלום, היי, מה שלומך) respond with a SQL statement that returns a friendly greeting text, for example: SELECT 'שלום! איך אפשר לעזור?' AS message.\n"
            "11. If the user asks about something unrelated to the available data, respond with SQL that returns 'אין לי מידע על זה' (e.g. SELECT 'אין לי מידע על זה' AS message) instead of trying to query non-existent tables.\n\n"
            "12. When the question mentions תחנה/תחנת/תחנות, use the sites table (column sites.name) to match station names rather than clients.\n\n"
            f"{reserved_instruction}"
            "🚫 ABSOLUTELY FORBIDDEN:\n"
            "- LIMIT clause anywhere in the query\n"
            "- DATE_SUB, INTERVAL, NOW(), CURDATE(), strftime()\n"
            "- OrdersBot2025 (wrong table name)\n"
            "- week column (use DATEPART(week, time) instead)\n"
            "- Reserved keywords as table aliases\n"
            f"{forbidden_functions}\n"
            "✅ REQUIRED SQL SERVER SYNTAX:\n"
            "- SELECT TOP N for limiting results\n"
            f"- Use tables: {', '.join(table_names)}\n"
            "- time column for dates in Orders\n"
            "- YEAR(time), MONTH(time), DATEPART(week, time)\n"
            "- GETDATE() for current date\n"
            "- DATEADD(day/week/month/year, number, date)\n"
            f"{allowed_functions}"
            f"{example_queries}"
            "EXAMPLE for top 10 customers:\n"
            "SELECT TOP 10 c.id, c.fname, c.lname, SUM(o.amount) as total\n"
            "FROM clients c JOIN lists l ON c.id = l.clientid\n"
            "JOIN Orders o ON l.id = o.listID\n"
            "GROUP BY c.id, c.fname, c.lname ORDER BY total DESC\n\n"
        )
        
        # Add conversation context if available
        if context_text.strip():
            base_prompt += (
                "Conversation context (use to resolve pronouns and follow-up references):\n"
                f"{context_text}\n"
                "When the question refers to items from the context, reuse the relevant filters and entities.\n"
            )
        
        base_prompt += (
            f"QUESTION (Hebrew): {question}\n\n"
            "Output: SQL query only."
        )
        
        return base_prompt

    def _select_relevant_tables(self, question: str) -> Dict[str, Any]:
        """Send full schema with Hebrew names and logical mapping"""
        tables_schema = {}
        
        for tname, meta in self.schema_info.get("tables", {}).items():
            # Include physical table info with Hebrew context
            table_info = {
                "physical_name": tname,
                "logical_name": meta.get("entity_name", tname),
                "display_name": meta.get("display_name", tname),
                "hebrew_names": meta.get("hebrew_names", []),
                "columns": []
            }
            
            # Add column information with Hebrew names
            for col in meta.get("columns", []):
                col_info = {
                    "physical_name": col["name"],
                    "logical_name": col.get("logical_name", col["name"]),
                    "type": col.get("type", "TEXT"),
                    "hebrew_names": col.get("hebrew_names", []),
                    "primary_key": col.get("primary_key", False)
                }
                table_info["columns"].append(col_info)
            
            tables_schema[tname] = table_info
        
        return tables_schema

    def _get_reserved_columns(self) -> List[str]:
        """Return schema columns that match SQL Server reserved keywords."""
        reserved: Set[str] = set()
        for table in self.schema_info.get("tables", {}).values():
            for column in table.get("columns", []) or []:
                name = column.get("name") or column.get("physical_name")
                if not name:
                    continue
                if name.upper() in SQLSERVER_RESERVED_KEYWORDS:
                    reserved.add(name)
        return sorted(reserved)

    def _call_openai_for_sql(self, prompt: str) -> str:
        sql_tokens = min(256, getattr(config, "MAX_TOKENS", 1000))
        
        # Simple messages - context is now in the prompt itself
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        logger.info(f"Sending to OpenAI with {len(messages)} total messages")
        logger.info(f"Sending to OpenAI - Prompt: {prompt[:200]}...")
        response = self.client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=messages,
            max_tokens=sql_tokens,
        )
        ai_content = response.choices[0].message.content
        logger.info(f"OpenAI returned: {ai_content}")
        
        if not ai_content or not ai_content.strip():
            logger.error("OpenAI returned empty response!")
            return '{"sql":"","tables":[],"description":"","error":"Empty response from OpenAI"}'
        
        return ai_content



    def _extract_json_block(self, text: str) -> Optional[str]:
        if not text:
            return None
        fence = re.search(r"```\s*json\s*(\{[\s\S]*?\})\s*```", text, re.IGNORECASE)
        if fence:
            return fence.group(1)
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start:end+1].strip()
        return None

    def _convert_limit_to_top(self, sql: str) -> str:
        """
        Convert MySQL/PostgreSQL LIMIT clause to SQL Server TOP clause.
        
        Examples:
        - SELECT * FROM table LIMIT 10 → SELECT TOP 10 * FROM table
        - SELECT id, name FROM users ORDER BY id LIMIT 5 → SELECT TOP 5 id, name FROM users ORDER BY id
        """
        import re
        
        # Pattern: LIMIT followed by a number at the end of query
        pattern = r'\bLIMIT\s+(\d+)\s*;?\s*$'
        match = re.search(pattern, sql, re.IGNORECASE)
        
        if match:
            limit_num = match.group(1)
            # Remove the LIMIT clause
            sql_without_limit = re.sub(pattern, '', sql, flags=re.IGNORECASE).strip()
            
            # Add TOP after SELECT
            sql_with_top = re.sub(
                r'\bSELECT\b',
                f'SELECT TOP {limit_num}',
                sql_without_limit,
                count=1,
                flags=re.IGNORECASE
            )
            
            logger.info(f"Converted LIMIT {limit_num} to TOP {limit_num}")
            return sql_with_top
        
        return sql

    def _extract_select_sql(self, text: str) -> Optional[str]:
        if not text:
            return None
        patterns = [
            r"(?is)\bselect\b[\s\S]+?\bfrom\b[\s\S]+?(?:;|$)",
            r"(?is)\bselect\b[\s\S]+?(?:;|$)",
        ]
        for pattern in patterns:
            m = re.search(pattern, text)
            if not m:
                continue
            candidate = m.group(0).strip()
            if len(candidate) < 10:
                continue
            return candidate
        return None

    def _parse_sql_response(self, content: str) -> Dict[str, Any]:
        logger.info(f"Parsing AI response: {content}")
        try:
            result = json.loads(content)
            sql_text = (result.get("sql") or "").strip()
            
            # ⚡ VALIDATE SQL SYNTAX - Check for forbidden SQLite/MySQL/PostgreSQL patterns
            if sql_text:
                # Auto-fix common mistakes before validation
                if "LIMIT" in sql_text.upper():
                    logger.warning("⚠️ Found LIMIT clause - auto-converting to TOP")
                    sql_text = self._convert_limit_to_top(sql_text)
                    result["sql"] = sql_text
                
                try:
                    validate_sql(sql_text, strict=True)
                    logger.info("✅ SQL validation passed - using only SQL Server syntax")
                except SQLValidationError as ve:
                    logger.error(f"❌ SQL validation failed: {ve.message}")
                    # Return error with helpful message
                    return {
                        "success": False,
                        "sql": "",
                        "tables": result.get("tables", []),
                        "description": result.get("description", ""),
                        "raw_response": content,
                        "error": f"Generated SQL contains forbidden syntax:\n{ve.message}",
                    }
            
            success = bool(sql_text)
            return {
                "success": success,
                "sql": sql_text,
                "tables": result.get("tables", []),
                "description": result.get("description", ""),
                "raw_response": content,
                "error": None if success else "Empty SQL in JSON response",
            }

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}. Raw response: {content[:200]}...")
            json_block = self._extract_json_block(content)
            if json_block:
                try:
                    result = json.loads(json_block)
                    sql_text = (result.get("sql") or "").strip()
                    success = bool(sql_text)
                    return {
                        "success": success,
                        "sql": sql_text,
                        "tables": result.get("tables", []),
                        "description": result.get("description", ""),
                        "raw_response": content,
                        "error": None if success else "Empty SQL in extracted JSON",
                    }
                except Exception as inner:
                    logger.warning(f"Extracted JSON block failed: {inner}. JSON block: {json_block[:100]}...")
            select_sql = self._extract_select_sql(content)
            if select_sql:
                # Auto-fix LIMIT to TOP before returning
                if "LIMIT" in select_sql.upper():
                    logger.warning("⚠️ Found LIMIT in extracted SQL - auto-converting to TOP")
                    select_sql = self._convert_limit_to_top(select_sql)
                try:
                    validate_sql(select_sql, strict=True)
                except SQLValidationError as ve:
                    logger.error(f"❌ SQL validation failed on extracted SQL: {ve.message}")
                    return {
                        "success": False,
                        "sql": "",
                        "tables": [],
                        "description": "",
                        "raw_response": content,
                        "error": f"Generated SQL contains forbidden syntax:\n{ve.message}",
                    }

                return {
                    "success": True,
                    "sql": select_sql,
                    "tables": [],
                    "description": "Extracted SQL from text",
                    "raw_response": content,
                    "error": None,
                }
            logger.error(f"Unable to parse response. Content length: {len(content) if content else 0}. First 100 chars: {content[:100] if content else 'None'}")
            return {
                "success": False,
                "sql": "",
                "tables": [],
                "description": "",
                "raw_response": content,
                "error": f"Unable to parse or extract SQL from model response. Content: {content[:200] if content else 'Empty'}",
            }

    def _apply_sql_fixes(self, sql: str) -> str:
        """Apply deterministic fixes to improve SQL reliability before execution."""
        if not sql:
            return sql

        parents_aliases: Set[str] = set()
        try:
            # Capture aliases from JOIN parents ...
            for match in re.finditer(r"JOIN\s+parents(?:\s+AS)?\s+([a-zA-Z_][\w]*)", sql, flags=re.IGNORECASE):
                alias = match.group(1)
                if alias:
                    parents_aliases.add(alias)

            # If the table is referenced without alias
            if re.search(r"JOIN\s+parents\b", sql, flags=re.IGNORECASE):
                parents_aliases.add("parents")

            def _wrap_week(match: re.Match[str]) -> str:
                token = match.group(0)
                # Avoid double wrapping
                if "TRY_CONVERT" in token.upper():
                    return token
                return f"TRY_CONVERT(int, {token})"

            for alias in parents_aliases:
                pattern = re.compile(rf"(?<!TRY_CONVERT\(int,\s*)(\b{alias}\s*\.\s*week\b)", re.IGNORECASE)
                sql = pattern.sub(lambda m: _wrap_week(m), sql)

            def _wrap_dateadd_with_datepart(s: str, pattern: re.Pattern[str], left: bool) -> str:
                def _extract_dateadd_expr(text: str, start_index: int) -> Tuple[str, int]:
                    depth = 0
                    i = start_index
                    while i < len(text):
                        ch = text[i]
                        if ch == '(':
                            depth += 1
                        elif ch == ')':
                            depth -= 1
                            if depth == 0:
                                return text[start_index:i + 1], i + 1
                        i += 1
                    return "", start_index

                offset = 0
                result = []
                while True:
                    match = pattern.search(s, offset)
                    if not match:
                        result.append(s[offset:])
                        break

                    result.append(s[offset:match.start()])
                    dateadd_start = match.start('dateadd')
                    dateadd_expr, end_index = _extract_dateadd_expr(s, dateadd_start)
                    if not dateadd_expr:
                        # Fallback: append original text and move on
                        result.append(s[match.start():match.end()])
                        offset = match.end()
                        continue

                    if left:
                        prefix = match.group('prefix')
                        replacement = f"{prefix}DATEPART(week, {dateadd_expr})"
                        offset = end_index
                    else:
                        suffix = match.group('suffix')
                        replacement = f"DATEPART(week, {dateadd_expr}) = {suffix}"
                        offset = match.end()
                    result.append(replacement)

                return ''.join(result)

            pattern_left = re.compile(
                r"(?P<prefix>TRY_CONVERT\(\s*int\s*,\s*[^)]+\)\s*=\s*)" r"(?P<dateadd>DATEADD\(\s*week\b)",
                re.IGNORECASE,
            )

            sql = _wrap_dateadd_with_datepart(sql, pattern_left, left=True)

            pattern_right = re.compile(
                r"(?P<dateadd>DATEADD\(\s*week\b)\s*=\s*(?P<suffix>TRY_CONVERT\(\s*int\s*,\s*[^)]+\))",
                re.IGNORECASE,
            )

            sql = _wrap_dateadd_with_datepart(sql, pattern_right, left=False)

            # Final sweep: wrap any remaining .week references to ensure safe int comparison
            sql = re.sub(
                r"(?<!TRY_CONVERT\(int,\s*)(\b[a-zA-Z_][\w]*\s*\.\s*week\b)",
                lambda m: _wrap_week(m),
                sql,
                flags=re.IGNORECASE,
            )

        except Exception:
            logger.exception("Failed to apply parents.week fix")

        return sql

    def _ensure_select_statement(self, sql: str) -> str:
        """Ensure the final SQL is an executable SELECT; wrap plain text as a constant result."""
        if not sql:
            return sql

        if re.search(r"\bselect\b", sql, flags=re.IGNORECASE):
            return sql

        message = sql.replace("'", "''").strip()
        if not message:
            message = "אין לי מידע על זה"
        return f"SELECT '{message}' AS message"

    def execute_query(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        start_time = time.perf_counter()
        try:
            # Auto-fix LIMIT to TOP as last resort before execution
            if "LIMIT" in sql.upper():
                logger.warning("⚠️ CRITICAL: Found LIMIT in SQL before execution - emergency fix to TOP")
                sql = self._convert_limit_to_top(sql)
            
            # Translate SQL functions to database-specific syntax
            sql = self._ensure_select_statement(sql)
            translated_sql = self.sql_generator.translate_sql_functions(sql)
            if translated_sql != sql:
                logger.info(f"Translated SQL: {sql} -> {translated_sql}")
                sql = translated_sql
            
            logger.debug(f"Executing SQL: {sql} | params={params or {}}")
            result = self.db.execute(text(sql), params or {})
            if sql.strip().lower().startswith("select"):
                columns = result.keys()
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
                elapsed = time.perf_counter() - start_time
                return {"success": True, "results": rows, "row_count": len(rows), "duration_sec": elapsed}
            else:
                self.db.commit()
                elapsed = time.perf_counter() - start_time
                return {"success": True, "row_count": result.rowcount, "message": f"Query executed in {elapsed:.2f} sec", "duration_sec": elapsed}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e), "duration_sec": time.perf_counter() - start_time}

    def generate_response(self, question: str, query_results: Dict[str, Any], context_text: str = "") -> str:
        """
        Generate natural language response in Hebrew.
        
        Args:
            question: User's question in Hebrew
            query_results: Query execution results
            context_text: Optional conversation context
            
        Returns:
            Natural language answer in Hebrew
        """
        start_time = time.perf_counter()
        try:
            sample = query_results.get("results", [])[:1]
            columns = list(sample[0].keys()) if sample else []
            
            base_prompt = (
                "Write exactly one short, clear, self-contained sentence in Hebrew that summarizes the main result. "
                "Respond in Hebrew only. Do not include code, lists, quotes, or multiple sentences. "
                "Explicitly mention the main business entity (e.g., customers, total sales, order count, product, week) "
                "and include the concrete values from the data (use numerals; apply thousands separators if appropriate). "
                "Do not write generic phrases like 'נמצאו X תוצאות' or 'הנתונים מצביעים על'; be specific and data-grounded.\n"
            )
            
            # Add conversation context if available
            if context_text.strip():
                base_prompt += context_text + "\n"
            
            base_prompt += (
                f"Question (Hebrew): {question}\n"
                f"Columns: {json.dumps(columns, ensure_ascii=False)}\n"
                f"Sample data (first row only): {json.dumps(sample, ensure_ascii=False, default=str)}\n"
                "Examples of phrasing style (do not copy verbatim):\n"
                "- For a total customer count: מספר הלקוחות הכולל הוא 1,234.\n"
                "- For a specific city: בעיר חיפה יש 1,137 לקוחות.\n"
                "- For weekly sales: בשבוע 12 נמכרו 980 יחידות.\n"
                "- For total orders: בוצעו 245 הזמנות חדשות.\n"
                "- For product performance: המוצר הנמכר ביותר הוא חולצת כותנה עם 512 יחידות.\n"
                "If there are zero rows, return a single Hebrew sentence stating that no results were found for the question."
            )
            
            ans_tokens = min(160, getattr(config, "MAX_TOKENS", 1000))
            try:
                response = self.client.chat.completions.create(
                    model=config.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You produce exactly one concise sentence in Hebrew that is fully self-contained and understandable without seeing the question. Return only the sentence, no lists, no code."},
                        {"role": "user", "content": base_prompt},
                    ],
                    max_tokens=ans_tokens,
                )
                ai_response = (response.choices[0].message.content or "").strip()
            except Exception as e:
                # Any OpenAI error (including network filters/HTML blocks) → deterministic fallback
                msg = (str(e) or "").lower()
                if "netfree" in msg or "<html" in msg:
                    logger.warning("OpenAI call appears blocked by network filter; using deterministic fallback.")
                # Deterministic fallback based on query results
                rows = query_results.get("results", [])
                rc = query_results.get("row_count", 0)
                if rc == 0:
                    return "לא נמצאו תוצאות לשאלה שלך."
                if rc == 1 and rows:
                    row = rows[0]
                    if len(row) == 1:
                        val = list(row.values())[0]
                        return str(val)
                    parts = [f"{k}: {v}" for k, v in row.items()]
                    return "התוצאה: " + ", ".join(parts)
                return f"התקבלו {rc} תוצאות עבור השאלה."
            elapsed = time.perf_counter() - start_time
            logger.info(f"🗣️ Response generation took {elapsed:.2f} sec")
            # If the first attempt is empty or too generic, try a stricter second pass
            def _too_generic(txt: str) -> bool:
                return (not txt) or txt.startswith("נמצאו ")

            if _too_generic(ai_response):
                prompt2 = (
                    "Write one short, clear sentence in Hebrew that is self-contained and includes the relevant values from the data. "
                    "Do not write 'נמצאו X תוצאות', do not write lists or code. Return exactly one specific sentence.\n"
                    f"השאלה: {question}\n"
                    f"עמודות: {json.dumps(columns, ensure_ascii=False)}\n"
                    f"דוגמה נתונים: {json.dumps(sample, ensure_ascii=False, default=str)}\n"
                )
                response2 = self.client.chat.completions.create(
                    model=config.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You produce exactly one concise, self-contained Hebrew sentence. No tables, no code."},
                        {"role": "user", "content": prompt2},
                    ],
                    max_tokens=ans_tokens,
                )
                ai_response2 = (response2.choices[0].message.content or "").strip()
                if not _too_generic(ai_response2):
                    return ai_response2

            # Last-resort deterministic fallback if model still failed
            explicit = self._format_explicit_answer(question, query_results)
            if explicit:
                return explicit
            rows = query_results.get("results", [])
            rc = query_results.get("row_count", 0)
            if rc == 0:
                return "לא נמצאו תוצאות לשאלה שלך."
            if rc == 1 and rows:
                row = rows[0]
                if len(row) == 1:
                    val = list(row.values())[0]
                    return str(val)
                # Multi-column single row: join key facts
                parts = []
                for k, v in row.items():
                    parts.append(f"{k}: {v}")
                return "התוצאה: " + ", ".join(parts)
            return f"התקבלו {rc} תוצאות עבור השאלה."
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(f"❌ Error generating response after {elapsed:.2f} sec: {str(e)}")
            return f"אירעה שגיאה ביצירת התשובה: {str(e)}"



    def _format_explicit_answer(self, question: str, query_results: Dict[str, Any]) -> Optional[str]:
        """
        Generate a natural-language answer in English using OpenAI:
        - If no results: return "No results found."
        - Otherwise: send the question and summarized query results (JSON) to OpenAI
        to generate a clear, short, human-readable answer.
        Notes:
        - Requires environment variable OPENAI_API_KEY
        - Uses self.nlg_model or OPENAI_NLG_MODEL (default: gpt-4o-mini)
        """
        import json

        rows = query_results.get("results") or []
        rc = query_results.get("row_count", len(rows) if isinstance(rows, list) else 0)

        if rc == 0:
            return "No results found."

        # Safely convert each row to a dictionary (works for SQLAlchemy Row objects as well)
        def row_to_dict(r):
            if isinstance(r, dict):
                return r
            try:
                return dict(r)
            except Exception:
                try:
                    return {k: r[k] for k in r.keys()}
                except Exception:
                    return {"value": str(r)}

        # Limit number of preview rows to keep the prompt short
        max_rows = 5
        preview_rows = [row_to_dict(r) for r in rows[:max_rows]]

        compact_context = {
            "row_count": rc,
            "preview": preview_rows,
        }

        # Build the OpenAI prompt
        user_prompt = (
            "You are a professional BI assistant. Based only on the SQL query results provided below "
            "in JSON format, generate a short and accurate Hebrew sentence that clearly answers the user’s question. "
            "Avoid technical terms, do not add data that doesn’t exist in the results, and be concise. "
            "If results are ambiguous or incomplete, phrase the response carefully (e.g., 'at least X'). "
            "After the main answer, add one short and natural follow-up question in Hebrew that encourages the user "
            "to continue exploring the data — for example, suggesting a forecast, breakdown, or trend analysis. "
            "The follow-up must be relevant to the topic of the question.\n\n"
            f"Question: \"{question}\"\n"
            f"Query Results (JSON): {json.dumps(compact_context, ensure_ascii=False, default=str)}"
            "Return only the Hebrew text (answer + follow-up question)."
        )

        try:
            # Send request to OpenAI
            import os
            from openai import OpenAI

            client = getattr(self, "openai_client", None) or OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            model = getattr(self, "nlg_model", os.getenv("OPENAI_NLG_MODEL", "gpt-4o-mini"))

            completion = client.chat.completions.create(
                model=model,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": "You are a clear, concise, and professional BI report summarizer."},
                    {"role": "user", "content": user_prompt},
                ],
            )

            text = completion.choices[0].message.content.strip()
            return text or None

        except Exception:
            # Graceful fallback: basic text representation of results
            try:
                if len(preview_rows) == 1 and len(preview_rows[0]) == 1:
                    val = next(iter(preview_rows[0].values()))
                    return f"The result is {val}."
                return f"Example results: {json.dumps(preview_rows, ensure_ascii=False, default=str)}"
            except Exception:
                return "Unable to generate a natural-language answer from the results."
