import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip()
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
CLIENT_ID = os.getenv("CLIENT_ID", "KT").strip()
META_SCHEMA_PATH = os.getenv("META_SCHEMA_PATH", "config/meta_schema.json").strip()
SEMANTIC_MAP_PATH= os.getenv("SEMANTIC_MAP_PATH", "config/semantic_map.json").strip()
if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY in .env")
if not DATABASE_URL:
    raise RuntimeError("Missing DATABASE_URL in .env")
if not CLIENT_ID:
    raise RuntimeError("Missing CLIENT_ID in .env")
