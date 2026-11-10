import asyncio

from src.rag.services.llm_provider_service import get_embedding_provider


async def embed_texts_service(texts: list[str]) -> list[list[float]]:
    return await asyncio.to_thread(lambda: get_embedding_provider().embed(texts))
