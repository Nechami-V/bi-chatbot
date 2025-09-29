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
    
    # Business Tables - tables to analyze for AI schema understanding
    BUSINESS_TABLES = ["ClientsBot2025", "OrdersBot2025", "ItemsBot2025", "SalesBot2025"]
    
    # System prompt for AI
    SYSTEM_PROMPT = """
You are an expert SQL assistant for a Hebrew Business Intelligence system.
Your job is to convert natural language questions in Hebrew to precise SQL queries.

DATABASE SCHEMA (SQLite):

Table: ClientsBot2025
- ID_לקוח (INTEGER, PRIMARY KEY) - customer ID
- lname (TEXT) - last name in Hebrew
- fname (TEXT) - first name in Hebrew  
- wname (TEXT) - wife name in Hebrew
- city (TEXT) - city name in Hebrew

Table: OrdersBot2025
- ID_מכירה (INTEGER, PRIMARY KEY) - sale ID
- ID_לקוח (INTEGER) - customer ID (links to ClientsBot2025.ID_לקוח)
- ID_פריט (INTEGER) - item ID (links to ItemsBot2025.ID_פריט)
- תאריך (TEXT) - date
- סכום (REAL) - amount/sum

Table: ItemsBot2025
- ID_פריט (INTEGER, PRIMARY KEY) - item ID
- name (TEXT) - item name in Hebrew
- pgrp (INTEGER) - product group

Table: SalesBot2025
- ID_מכירה (INTEGER, PRIMARY KEY) - sale ID
- week (TEXT) - week
- name (TEXT) - name

CRITICAL SQL RULES:
1. Use Hebrew column names as they exist in the database
2. Hebrew text should appear in WHERE conditions for data matching
3. Use proper SQLite syntax (no unsupported functions)
4. Always use proper JOINs when needed
5. Use COUNT(*), SUM(), AVG() etc. with English aliases for results
6. For city matching, be aware of variations (מודיעין עילית, מודיעין עלית, etc.)

RESPONSE FORMAT - Return ONLY valid JSON:
{
  "sql": "SELECT COUNT(*) AS customer_count FROM ClientsBot2025 WHERE city = 'מודיעין עילית'",
  "tables": ["ClientsBot2025"],
  "description": "ספירת לקוחות במודיעין עילית"
}

COMMON HEBREW TO SQL MAPPINGS:
- "כמה לקוחות" → COUNT(*) AS customer_count FROM ClientsBot2025
- "סך הכל מכירות" → SUM(סכום) AS total_sales FROM OrdersBot2025
- "ממוצע" → AVG() 
- "עיר" → city in ClientsBot2025
- "לקוח" → ClientsBot2025
- "הזמנה/מכירה" → OrdersBot2025
- "פריט" → ItemsBot2025

Remember: Use the actual Hebrew column names that exist in the database!
"""

# Create global config instance
config = Config()