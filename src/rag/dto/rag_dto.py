from dataclasses import dataclass, field


@dataclass
class Chunk:
    """A piece of text that always travels with its metadata (file_id, filename, collection_id, chunk_index...)."""
    text: str
    metadata: dict = field(default_factory=dict)


@dataclass
class RetrievedChunk(Chunk):
    """A chunk returned by retrieval, with its cosine distance to the question (lower is closer)."""
    distance: float = 0.0
