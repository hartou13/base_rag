import asyncio
from typing import AsyncIterator

from starlette.concurrency import iterate_in_threadpool

from src.rag.dto.rag_dto import Chunk
from src.rag.services.llm_provider_service import get_chat_provider


def build_messages(question: str, chunks: list[Chunk], history: list[dict] | None = None) -> list[dict]:
    """Past turns of the session (memory) followed by the new question with its passages."""
    passages = "\n\n".join(f"Passage {i + 1}:\n{c.text}" for i, c in enumerate(chunks))
    current = {"role": "user", "content": (
        "Answer the question using only the passages below. Do not use outside knowledge. "
        "Earlier messages of this conversation are given for context. "
        "If the passages do not contain the answer, say so.\n\n"
        f"Question: {question}\n\n{passages}")}
    return [*(history or []), current]


async def generate_answer_service(question: str, chunks: list[Chunk], history: list[dict] | None = None) -> str:
    """Generation only: takes the question and already-retrieved chunks, returns the answer text."""
    messages = build_messages(question, chunks, history)
    return await asyncio.to_thread(lambda: get_chat_provider().chat(messages))


async def generate_answer_stream_service(
    question: str, chunks: list[Chunk], history: list[dict] | None = None
) -> AsyncIterator[str]:
    """Streaming generation: yields answer text pieces as the model produces them."""
    messages = build_messages(question, chunks, history)
    async for piece in iterate_in_threadpool(get_chat_provider().chat_stream(messages)):
        yield piece
