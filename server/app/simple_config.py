import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path('.') / '.env'
load_dotenv(env_path)


def _load_business_tables_from_yaml() -> list[str]:
  default_tables = [
    "ClientsBot2025",
    "OrdersBot2025",
    "ItemsBot2025",
    "SalesBot2025",
  ]
  schemas_dir = os.getenv("SCHEMAS_DIR", "configs/schemas").strip()
  meta_schema_path = Path(schemas_dir) / "META_SCHEMA.yaml"

  try:
    with open(meta_schema_path, "r", encoding="utf-8") as handle:
      meta_schema = yaml.safe_load(handle) or {}
    tables = meta_schema.get("tables")
    if isinstance(tables, dict):
      ordered_tables = list(tables.keys())
      if ordered_tables:
        return ordered_tables
  except Exception:
    pass

  return default_tables

class Config:
    """Simple configuration manager for the BI Chatbot"""

    # --- OpenAI Settings ---
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
    OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "3"))
    OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "30"))

    # --- AI Parameters ---
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))

    # --- Database Settings ---
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/bi_database.db")
    METADATA_DATABASE_URL = os.getenv(
        "METADATA_DATABASE_URL",
        "mssql+pyodbc://@SPBYTES/AI?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes",
    )
    # External Users DB (e.g., SQL Server via pyodbc)
    USER_DATABASE_URL = os.getenv("USER_DATABASE_URL", "mssql+pyodbc://@localhost\\SQLEXPRESS/CHATBOTBI?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes")
    # Optional overrides for external users table/columns
    USER_TABLE_NAME = os.getenv("USER_TABLE_NAME", "users")
    USER_TABLE_SCHEMA = os.getenv("USER_TABLE_SCHEMA", "")
    USER_COL_ID = os.getenv("USER_COL_ID", "")
    USER_COL_EMAIL = os.getenv("USER_COL_EMAIL", "")
    USER_COL_PASSWORD = os.getenv("USER_COL_PASSWORD", "")
    USER_COL_FIRST_NAME = os.getenv("USER_COL_FIRST_NAME", "")
    USER_COL_LAST_NAME = os.getenv("USER_COL_LAST_NAME", "")
    USER_COL_PHONE = os.getenv("USER_COL_PHONE", "")
    USER_COL_IS_MANAGER = os.getenv("USER_COL_IS_MANAGER", "")
    USER_COL_PERMISSION_GROUP = os.getenv("USER_COL_PERMISSION_GROUP", "")

    # --- Security / Auth ---
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
    
    # --- Development Mode: Disable Authentication ---
    # Set DISABLE_AUTH=true in .env to bypass authentication (for testing/development)
    DISABLE_AUTH = os.getenv("DISABLE_AUTH", "false").lower() in ("true", "1", "yes")

    # --- Business Tables ---
  BUSINESS_TABLES = _load_business_tables_from_yaml()

    # --- System Prompt  ---
    SYSTEM_PROMPT = """
  You are a professional Business Intelligence expert. Your goal is to understand a user’s natural-language
  question and translate it into the most accurate SQL query possible — based only on the data structure that
  exists in the client’s database. Carefully analyze the question, identify which tables and fields are 
  relevant according to the provided schema and mapping, and build a complete, precise SQL query that can directly
  answer it. The query must follow the exact syntax and conventions of the specific database type (for example: SQL Server, 
  PostgreSQL, MySQL, or SQLite), according to the version provided. If the question cannot be answered with the available
  tables or data — even after checking the mapping table — respond clearly that the question does not match the client’s 
  available data. Return **only** the SQL query itself, with no explanations, comments, or additional text. Your purpose is 
  to give the client the **most accurate, reliable, and professional** query possible for every question they ask.
  """

    # --- Prompt Packs ---
    # Active pack name (required by product request). If not set, code should raise a clear error.
    PACK = os.getenv("PACK", "").strip()
    PROMPTS_DIR = os.getenv("PROMPTS_DIR", "configs/prompts").strip()
    SCHEMAS_DIR = os.getenv("SCHEMAS_DIR", "configs/schemas").strip()
# Global config instance
config = Config()
