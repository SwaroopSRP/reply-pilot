"""Application configuration settings loaded from environment variables and .env file."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
DB_PATH = DATA_DIR / "replypilot.db"
CHROMA_DIR = DATA_DIR / "chroma"

# Ensure essential data directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")


class Settings:
    """Central configuration for ReplyPilot."""

    # LLM Provider Configuration
    # Supports Gemini API (google-genai / langchain-google-genai)
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))

    # Vector store & Embeddings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    CHROMA_COLLECTION: str = "replypilot_knowledge"

    # Database
    DATABASE_PATH: Path = DB_PATH
    KNOWLEDGE_PATH: Path = KNOWLEDGE_DIR
    CHROMA_PATH: Path = CHROMA_DIR


settings = Settings()
