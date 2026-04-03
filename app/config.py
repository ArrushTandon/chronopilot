import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3-flash-preview"

DB_HOST = os.environ.get("DB_HOST")
DB_PORT = int(os.environ.get("DB_PORT", 5432))
DB_NAME = os.environ.get("DB_NAME", "deadline_survival")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS = os.environ.get("DB_PASS", "alloydb")

# Your test user UUID from the seed step
DEFAULT_USER_ID = os.environ.get("DEFAULT_USER_ID", "")