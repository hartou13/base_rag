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
OLLAMA_CLOUD_HOST = os.environ.get("OLLAMA_CLOUD_HOST", "https://ollama.com")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "qwen3-embedding")
CHAT_MODEL = os.environ.get("CHAT_MODEL", "gemma4:31b")
CHAT_FALLBACK_MODEL = os.environ.get("CHAT_FALLBACK_MODEL", "gemma4:31b")

# Storage
CHROMA_PATH = os.environ.get("CHROMA_PATH", str(BASE_DIR / "data" / "chroma"))
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", str(BASE_DIR / "data" / "uploads"))

# Pipeline
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "100"))
TOP_K = int(os.environ.get("TOP_K", "3"))
CHAT_HISTORY_LIMIT = int(os.environ.get("CHAT_HISTORY_LIMIT", "20"))  # past messages sent to the model
