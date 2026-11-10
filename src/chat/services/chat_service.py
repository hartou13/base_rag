import json
from typing import AsyncIterator

from fastapi import HTTPException

from src.chat.dto.chat_dto import ChatRequestDto
from src.collections.services.collection_service import (
    count_ready_files_service,
    get_owned_collection_service,
)
from src.rag.services import rag_config as cfg
from src.rag.services.generation_service import generate_answer_stream_service
from src.rag.services.llm_provider_service import LLMProviderError
from src.rag.services.retrieval_service import retrieve_service
from src.sessions.services.session_service import (
    add_messages_service,
    get_owned_session_service,
    get_recent_messages_service,
)


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


async def chat_service(data: ChatRequestDto, user_id: str) -> AsyncIterator[str]:
    """Validates and retrieves up front (errors surface as normal HTTP errors),
    then returns an async generator of SSE events: sources, token*, done | error.
    The session's stored history is sent to the model; the new turn is saved once the answer is complete."""
    session = await get_owned_session_service(data.session_id, user_id)
    collection_id = data.collection_id
    await get_owned_collection_service(collection_id, user_id)
    if await count_ready_files_service(collection_id) == 0:
        raise HTTPException(status_code=409, detail="Collection has no indexed files yet")
    history = await get_recent_messages_service(session.id, cfg.CHAT_HISTORY_LIMIT)
    try:
        chunks = await retrieve_service(collection_id, data.question)
    except LLMProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))
    sources = [
        {
            "file_id": c.metadata.get("file_id"),
            "filename": c.metadata.get("filename"),
            "text": c.text,
            "distance": c.distance,
        }
        for c in chunks
    ]

    async def event_stream() -> AsyncIterator[str]:
        yield _sse({"type": "sources", "sources": sources})
        answer_parts: list[str] = []
        try:
            async for piece in generate_answer_stream_service(data.question, chunks, history):
                answer_parts.append(piece)
                yield _sse({"type": "token", "content": piece})
        except LLMProviderError as e:
            yield _sse({"type": "error", "detail": str(e)})
            return
        # Only a completed answer is stored, so history never holds an unanswered question.
        await add_messages_service(
            session.id, [("user", data.question), ("assistant", "".join(answer_parts))]
        )
        yield _sse({"type": "done"})

    return event_stream()
