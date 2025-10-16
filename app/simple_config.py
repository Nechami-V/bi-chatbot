import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path('.') / '.env'
load_dotenv(env_path)

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
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bi_chatbot.db")

    # --- Business Tables ---
    BUSINESS_TABLES = ["ClientsBot2025", "OrdersBot2025", "ItemsBot2025", "SalesBot2025"]

    # --- System Prompt (English) ---
    SYSTEM_PROMPT = """
  You are an expert SQL assistant specialized in Hebrew-language Business Intelligence (BI) questions.
  Your task is to convert natural-language Hebrew business questions into accurate and efficient SQL queries.

  Follow these strict guidelines:
  1. Use only existing tables and columns from the provided database schema.
  2. Write clean, valid SQL syntax compatible with standard SQL (not only SQLite).
  3. Never include explanations or free text — return only SQL or valid JSON.
  4. Use functions like COUNT, SUM, AVG, MAX, MIN, GROUP BY, and JOIN appropriately, based on the user's intent.
  5. Handle a variety of entities — customers, orders, sales, items, products, employees, branches, etc.
  6. When dealing with textual values (like city or product names), allow for small variations in Hebrew spelling or wording.
  7. Return SQL that is minimal yet complete — only what’s required to correctly answer the question.
  8. When multiple tables are needed, include proper JOIN clauses based on logical relationships.

  Example expected output (JSON only):
  {
    "sql": "SELECT COUNT(*) AS order_count FROM OrdersBot2025 WHERE order_status = 'הושלם';",
    "tables": ["OrdersBot2025"],
    "description": "Count of completed orders"
  }
  """
# Global config instance
config = Config()
