"""Provider-agnostic interfaces for embeddings and chat.

The rest of the application only uses these interfaces. A provider (Ollama today)
implements them in its own file, and is selected by EMBED_PROVIDER / CHAT_PROVIDER.
To add a provider: implement the two classes below, then register it in the factories.
"""
from abc import ABC, abstractmethod
from typing import Iterator

from src.rag.services import rag_config as cfg


class LLMProviderError(Exception):
    """Raised by any provider; carries a readable message for the API."""


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per text."""


class ChatProvider(ABC):
    @abstractmethod
    def chat(self, messages: list[dict]) -> str:
        """Send chat messages ({"role", "content"}) and return the answer text."""

    @abstractmethod
    def chat_stream(self, messages: list[dict]) -> Iterator[str]:
        """Send chat messages and yield the answer text piece by piece."""


_embedding_provider = None
_chat_provider = None


def get_embedding_provider() -> EmbeddingProvider:
    global _embedding_provider
    if _embedding_provider is None:
        if cfg.EMBED_PROVIDER == "ollama":
            from src.rag.services.ollama_provider_service import OllamaEmbeddingProvider
            _embedding_provider = OllamaEmbeddingProvider()
        else:
            raise LLMProviderError(f"Unknown EMBED_PROVIDER '{cfg.EMBED_PROVIDER}'")
    return _embedding_provider


def get_chat_provider() -> ChatProvider:
    global _chat_provider
    if _chat_provider is None:
        if cfg.CHAT_PROVIDER == "ollama":
            from src.rag.services.ollama_provider_service import OllamaChatProvider
            _chat_provider = OllamaChatProvider()
        else:
            raise LLMProviderError(f"Unknown CHAT_PROVIDER '{cfg.CHAT_PROVIDER}'")
    return _chat_provider
