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
# Global config instance
config = Config()
