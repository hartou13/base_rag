from src.rag.dto.rag_dto import RetrievedChunk
from src.rag.services import rag_config as cfg
from src.rag.services.embedding_service import embed_texts_service
from src.rag.services.vector_store_service import query_chunks_service


async def retrieve_service(collection_id: str, question: str, top_k: int = None) -> list[RetrievedChunk]:
    """Retrieval only: question in, nearest chunks (with metadata and distance) out. No generation."""
    embedding = (await embed_texts_service([question]))[0]
    return await query_chunks_service(collection_id, embedding, top_k or cfg.TOP_K)
