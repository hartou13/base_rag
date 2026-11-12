import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[3]

# Which implementation is used behind each interface (see llm_provider_service.py)
EMBED_PROVIDER = os.environ.get("EMBED_PROVIDER", "ollama")
CHAT_PROVIDER = os.environ.get("CHAT_PROVIDER", "ollama")

# Ollama
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY", "")
OLLAMA_LOCAL_HOST = os.environ.get("OLLAMA_LOCAL_HOST", "http://127.0.0.1:11434")
OLLAMA_CLOUD_HOST = os.environ.get("OLLAMA_CLOUD_HOST", "http://127.0.0.1:11434")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "qwen3-embedding")
CHAT_MODEL = os.environ.get("CHAT_MODEL", "gemma4:e4b")
CHAT_FALLBACK_MODEL = os.environ.get("CHAT_FALLBACK_MODEL", "gemma4:e4b")

# Storage
CHROMA_PATH = os.environ.get("CHROMA_PATH", str(BASE_DIR / "data" / "chroma"))
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", str(BASE_DIR / "data" / "uploads"))

# Pipeline
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "100"))
TOP_K = int(os.environ.get("TOP_K", "3"))
CHAT_HISTORY_LIMIT = int(os.environ.get("CHAT_HISTORY_LIMIT", "20"))  # past messages sent to the model

# Security
MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_BYTES", str(20 * 1024 * 1024)))
MAX_PDF_PAGES = int(os.environ.get("MAX_PDF_PAGES", "200"))
FILE_URL_SECRET = os.environ.get("FILE_URL_SECRET", "")  # required at startup (see main.py)
FILE_URL_TTL_SECONDS = int(os.environ.get("FILE_URL_TTL_SECONDS", "300"))
FILE_URL_SINGLE_USE = os.environ.get("FILE_URL_SINGLE_USE", "false").lower() == "true"
# Hosts allowed for links/images in answers; empty = strip every external link and image.
ALLOWED_LINK_DOMAINS = [d.strip().lower() for d in os.environ.get("ALLOWED_LINK_DOMAINS", "").split(",") if d.strip()]
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
LOG_DIR = os.environ.get("LOG_DIR", str(BASE_DIR / "data" / "logs"))
LOG_RETENTION_DAYS = int(os.environ.get("LOG_RETENTION_DAYS", "30"))
