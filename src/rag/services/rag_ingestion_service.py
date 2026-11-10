import asyncio
from pathlib import Path

from pypdf import PdfReader

from src.rag.dto.rag_dto import Chunk
from src.rag.services import rag_config as cfg
from src.rag.services.embedding_service import embed_texts_service
from src.rag.services.vector_store_service import add_chunks_service

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}


def read_file(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(str(path))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    return path.read_text(encoding="utf-8", errors="replace")


def chunk_text(text: str, metadata: dict, size: int = None, overlap: int = None) -> list[Chunk]:
    """Split text into overlapping chunks; each chunk gets a copy of metadata plus its index."""
    size = size or cfg.CHUNK_SIZE
    overlap = cfg.CHUNK_OVERLAP if overlap is None else overlap
    step = size - overlap
    chunks = []
    for start in range(0, len(text), step):
        piece = text[start:start + size]
        if piece.strip():
            chunks.append(Chunk(text=piece, metadata={**metadata, "chunk_index": len(chunks), "start": start}))
        if start + size >= len(text):
            break
    return chunks


async def ingest_file_service(collection_id: str, file_id: str, filename: str, path: Path) -> int:
    text = await asyncio.to_thread(read_file, path)
    chunks = chunk_text(text, {"file_id": file_id, "filename": filename, "collection_id": collection_id})
    if not chunks:
        raise ValueError("No text could be extracted from the file.")
    embeddings = await embed_texts_service([c.text for c in chunks])
    await add_chunks_service(collection_id, chunks, embeddings)
    return len(chunks)
