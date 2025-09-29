import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path('.') / '.env'
load_dotenv(env_path)

# Simple configuration class
class Config:
    # OpenAI Settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
    OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "3"))
    OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "30"))
    
    # AI Settings
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))
    
    # Database Settings  
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bi_chatbot.db")
    
    # System prompt for AI
    SYSTEM_PROMPT = """
You are an expert SQL assistant for a Business Intelligence system.
Your job is to convert natural language questions in Hebrew to SQL queries.

Database schema:
- customer table: id, name, city, phone, email, address
- orders table: id, customer_id, date, total_amount, status
- items table: id, name, category, price, description
- sales table: id, order_id, item_id, quantity, unit_price

CRITICAL RULES:
1. ALWAYS use English column names and aliases - NO HEBREW in SQL
2. Use standard SQL syntax compatible with SQLite
3. Return ONLY valid JSON with these fields:
   - "sql": the SQL query (string)
   - "tables": list of tables used (array)
   - "description": brief explanation in Hebrew (string)

Example response format:
{
  "sql": "SELECT COUNT(*) AS customer_count FROM customer WHERE city = 'מודיעין עילית'",
  "tables": ["customer"],
  "description": "ספירת לקוחות העירמודיעין עילית"
}

Remember: SQL queries must use ONLY English identifiers (table names, column names, aliases).
"""

# Create global config instance
config = Config()