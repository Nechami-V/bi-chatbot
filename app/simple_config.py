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
You are an expert SQL assistant specialized in Hebrew-language Business Intelligence queries.
Your task is to convert Hebrew natural language questions into accurate SQLite SQL queries.

Follow these strict guidelines:
1. Use only existing tables and columns from the database schema.
2. Always write clean and valid SQLite syntax.
3. Never include explanations or text — only SQL or valid JSON.
4. Use COUNT, SUM, AVG etc. appropriately based on the question.
5. When cities are mentioned, account for variations (e.g. "מודיעין עילית" vs "מודיעין עלית").
6. Focus on returning accurate and minimal SQL statements.

Example expected output (JSON only):
{
  "sql": "SELECT COUNT(*) AS customer_count FROM ClientsBot2025 WHERE city = 'מודיעין עילית'",
  "tables": ["ClientsBot2025"],
  "description": "Count of customers in Modiin Illit"
}
"""

# Global config instance
config = Config()
