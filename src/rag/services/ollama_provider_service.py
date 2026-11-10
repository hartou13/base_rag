"""Ollama implementation of the provider interfaces. Only this file imports ollama."""
import ssl
from typing import Iterator

from ollama import Client, ResponseError

from src.rag.services import rag_config as cfg
from src.rag.services.llm_provider_service import ChatProvider, EmbeddingProvider, LLMProviderError

CHAT_ERRORS = {
    401: "Ollama Cloud: OLLAMA_API_KEY is missing or wrong.",
    402: "Ollama Cloud: payment or credits needed.",
    429: "Ollama Cloud: usage limit reached.",
}


class OllamaEmbeddingProvider(EmbeddingProvider):
    def __init__(self):
        self._client = Client(host=cfg.OLLAMA_LOCAL_HOST, verify=ssl.create_default_context())
        self._model = None

    def _choose_model(self) -> str:
        if self._model is None:
            names = [m.model for m in self._client.list().models if m.model and "embed" in m.model.lower()]
            if not names:
                raise LLMProviderError("No embedding model found in the local Ollama model list.")
            self._model = next((n for n in names if n.split(":")[0] == cfg.EMBED_MODEL), names[0])
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        try:
            response = self._client.embed(model=self._choose_model(), input=list(texts))
        except ResponseError as e:
            raise LLMProviderError(str(e)) from e
        return [list(map(float, e)) for e in response.embeddings]


class OllamaChatProvider(ChatProvider):
    def __init__(self):
        if not cfg.OLLAMA_API_KEY:
            raise LLMProviderError("OLLAMA_API_KEY is not set.")
        self._client = Client(
            host=cfg.OLLAMA_CLOUD_HOST,
            headers={"Authorization": "Bearer " + cfg.OLLAMA_API_KEY},
            verify=ssl.create_default_context(),
        )

    def chat(self, messages: list[dict]) -> str:
        try:
            try:
                response = self._client.chat(model=cfg.CHAT_MODEL, messages=messages)
            except ResponseError as e:
                if e.status_code != 404:
                    raise
                response = self._client.chat(model=cfg.CHAT_FALLBACK_MODEL, messages=messages)
        except ResponseError as e:
            raise LLMProviderError(CHAT_ERRORS.get(e.status_code, str(e))) from e
        return response.message.content

    def _stream_model(self, model: str, messages: list[dict]) -> Iterator[str]:
        for part in self._client.chat(model=model, messages=messages, stream=True):
            if part.message.content:
                yield part.message.content

    def chat_stream(self, messages: list[dict]) -> Iterator[str]:
        started = False
        try:
            try:
                for piece in self._stream_model(cfg.CHAT_MODEL, messages):
                    started = True
                    yield piece
            except ResponseError as e:
                if e.status_code != 404 or started:
                    raise
                yield from self._stream_model(cfg.CHAT_FALLBACK_MODEL, messages)
        except ResponseError as e:
            raise LLMProviderError(CHAT_ERRORS.get(e.status_code, str(e))) from e
