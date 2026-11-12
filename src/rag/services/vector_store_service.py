"""Vector store wrapper. Only this file imports chromadb; swap the body to change store.

Every function works with Chunk / RetrievedChunk objects, so metadata always stays with the text.
"""
import asyncio

import chromadb

from src.rag.dto.rag_dto import Chunk, RetrievedChunk
from src.rag.services import rag_config as cfg

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=cfg.CHROMA_PATH)
    return _client


def _add_chunks(collection_id: str, chunks: list[Chunk], embeddings: list[list[float]]):
    collection = _get_client().get_or_create_collection(
        name=collection_id,
        configuration={"hnsw": {"space": "cosine"}},
        embedding_function=None,
    )
    collection.upsert(
        ids=[f"{c.metadata['file_id']}:{c.metadata['chunk_index']}" for c in chunks],
        embeddings=embeddings,
        documents=[c.text for c in chunks],
        metadatas=[c.metadata for c in chunks],
    )


def _query_chunks(collection_id: str, embedding: list[float], top_k: int) -> list[RetrievedChunk]:
    collection = _get_client().get_collection(collection_id)
    result = collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    return [
        RetrievedChunk(text=text, metadata=dict(metadata), distance=distance, id=chunk_id)
        for chunk_id, text, metadata, distance in zip(
            result["ids"][0], result["documents"][0], result["metadatas"][0], result["distances"][0]
        )
    ]


def _get_chunks_by_ids(collection_id: str, ids: list[str]) -> dict[str, Chunk]:
    try:
        result = _get_client().get_collection(collection_id).get(ids=ids, include=["documents", "metadatas"])
    except Exception:
        return {}  # collection deleted
    return {
        chunk_id: Chunk(text=text, metadata=dict(metadata))
        for chunk_id, text, metadata in zip(result["ids"], result["documents"], result["metadatas"])
    }


def _delete_collection(collection_id: str):
    try:
        _get_client().delete_collection(collection_id)
    except Exception:
        pass  # collection never received any chunk


def _delete_file_vectors(collection_id: str, file_id: str):
    try:
        _get_client().get_collection(collection_id).delete(where={"file_id": file_id})
    except Exception:
        pass  # collection never received any chunk


async def add_chunks_service(collection_id: str, chunks: list[Chunk], embeddings: list[list[float]]):
    await asyncio.to_thread(_add_chunks, collection_id, chunks, embeddings)


async def query_chunks_service(collection_id: str, embedding: list[float], top_k: int) -> list[RetrievedChunk]:
    return await asyncio.to_thread(_query_chunks, collection_id, embedding, top_k)


async def get_chunks_by_ids_service(collection_id: str, ids: list[str]) -> dict[str, Chunk]:
    """id -> Chunk for the ids that still exist (deleted files' chunks are simply absent)."""
    if not ids:
        return {}
    return await asyncio.to_thread(_get_chunks_by_ids, collection_id, ids)


async def delete_collection_vectors_service(collection_id: str):
    await asyncio.to_thread(_delete_collection, collection_id)


async def delete_file_vectors_service(collection_id: str, file_id: str):
    await asyncio.to_thread(_delete_file_vectors, collection_id, file_id)
