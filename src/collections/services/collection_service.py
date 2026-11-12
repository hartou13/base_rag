import shutil
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy import delete, func, select

from src.collections.dto.collection_dto import CollectionDto, CollectionFileDto, CreateCollectionDto
from src.collections.models.collection import Collection
from src.collections.models.collection_file import CollectionFile
from src.database.mysql_connector import get_db
from src.rag.services import rag_config as cfg
from src.collections.services.upload_validation_service import read_limited, validate_upload
from src.rag.services.rag_ingestion_service import ingest_file_service
from src.rag.services.vector_store_service import delete_collection_vectors_service, delete_file_vectors_service


def _to_dto(c: Collection, file_count: int = 0) -> CollectionDto:
    return CollectionDto(id=c.id, name=c.name, description=c.description, created_at=c.created_at,
                         file_count=file_count or 0)


def _file_to_dto(f: CollectionFile) -> CollectionFileDto:
    return CollectionFileDto(
        id=f.id, filename=f.filename, status=f.status, chunk_count=f.chunk_count or 0, error=f.error,
        content_type=f.content_type, size=f.size or 0, created_at=f.created_at,
    )


def _stored_path(collection_id: str, file_id: str) -> Path | None:
    """Uploaded files are stored as {UPLOAD_DIR}/{collection_id}/{file_id}{ext} (legacy: {file_id}_{filename})."""
    return next((Path(cfg.UPLOAD_DIR) / collection_id).glob(f"{file_id}*"), None)


async def get_owned_collection_service(collection_id: str, user_id: str) -> Collection:
    async with get_db() as session:
        result = await session.execute(
            select(Collection).where(Collection.id == collection_id, Collection.user_id == user_id)
        )
        collection = result.scalar_one_or_none()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection


async def get_owned_file_service(file_id: str, user_id: str) -> CollectionFile:
    async with get_db() as session:
        result = await session.execute(
            select(CollectionFile)
            .join(Collection, Collection.id == CollectionFile.collection_id)
            .where(CollectionFile.id == file_id, Collection.user_id == user_id)
        )
        db_file = result.scalar_one_or_none()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    return db_file


async def count_ready_files_service(collection_id: str) -> int:
    async with get_db() as session:
        result = await session.execute(
            select(func.count()).select_from(CollectionFile).where(
                CollectionFile.collection_id == collection_id, CollectionFile.status == "ready"
            )
        )
        return result.scalar_one()


async def create_collection_service(user_id: str, data: CreateCollectionDto) -> CollectionDto:
    async with get_db() as session:
        collection = Collection(id=str(uuid.uuid4()), user_id=user_id, name=data.name, description=data.description)
        session.add(collection)
        await session.flush()
        await session.refresh(collection)
        return _to_dto(collection)


async def list_collections_service(user_id: str) -> list[CollectionDto]:
    async with get_db() as session:
        result = await session.execute(
            select(Collection, func.count(CollectionFile.id))
            .outerjoin(CollectionFile, CollectionFile.collection_id == Collection.id)
            .where(Collection.user_id == user_id)
            .group_by(Collection.id)
            .order_by(Collection.created_at.desc())
        )
        return [_to_dto(c, count) for c, count in result.all()]


async def delete_collection_service(collection_id: str, user_id: str):
    await get_owned_collection_service(collection_id, user_id)
    await delete_collection_vectors_service(collection_id)
    shutil.rmtree(Path(cfg.UPLOAD_DIR) / collection_id, ignore_errors=True)
    async with get_db() as session:
        await session.execute(delete(CollectionFile).where(CollectionFile.collection_id == collection_id))
        await session.execute(delete(Collection).where(Collection.id == collection_id))
    return {"message": "Collection deleted"}


async def list_files_service(collection_id: str, user_id: str) -> list[CollectionFileDto]:
    await get_owned_collection_service(collection_id, user_id)
    async with get_db() as session:
        result = await session.execute(
            select(CollectionFile)
            .where(CollectionFile.collection_id == collection_id)
            .order_by(CollectionFile.created_at.desc())
        )
        return [_file_to_dto(f) for f in result.scalars().all()]


async def get_file_content_service(file_id: str, user_id: str) -> tuple[Path, CollectionFile]:
    db_file = await get_owned_file_service(file_id, user_id)
    path = _stored_path(db_file.collection_id, file_id)
    if not path or not path.is_file():
        raise HTTPException(status_code=404, detail="The stored file is missing")
    return path, db_file


async def delete_file_service(file_id: str, user_id: str):
    db_file = await get_owned_file_service(file_id, user_id)
    collection_id = db_file.collection_id
    await delete_file_vectors_service(collection_id, file_id)
    for path in (Path(cfg.UPLOAD_DIR) / collection_id).glob(f"{file_id}*"):
        path.unlink(missing_ok=True)
    async with get_db() as session:
        await session.execute(delete(CollectionFile).where(CollectionFile.id == file_id))
    return {"message": "File deleted"}


async def _index_file(collection_id: str, file_id: str, filename: str, path: Path) -> CollectionFileDto:
    """Run ingestion for a stored file and record the outcome on its row."""
    try:
        chunk_count = await ingest_file_service(collection_id, file_id, filename, path)
        status, error = "ready", None
    except Exception as e:
        chunk_count, status, error = 0, "failed", str(e)
    async with get_db() as session:
        db_file = await session.get(CollectionFile, file_id)
        db_file.status, db_file.chunk_count, db_file.error = status, chunk_count, error
        await session.flush()
        await session.refresh(db_file)
        return _file_to_dto(db_file)


async def reindex_file_service(file_id: str, user_id: str) -> CollectionFileDto:
    db_file = await get_owned_file_service(file_id, user_id)
    if db_file.status == "indexing":
        raise HTTPException(status_code=409, detail="This file is already being indexed")
    path = _stored_path(db_file.collection_id, file_id)
    if not path or not path.is_file():
        raise HTTPException(status_code=404, detail="The stored file is missing; upload it again")
    async with get_db() as session:
        row = await session.get(CollectionFile, file_id)
        row.status, row.error, row.chunk_count = "indexing", None, 0
    await delete_file_vectors_service(db_file.collection_id, file_id)
    return await _index_file(db_file.collection_id, file_id, db_file.filename, path)


async def add_files_service(collection_id: str, user_id: str, files: list[UploadFile]) -> list[CollectionFileDto]:
    await get_owned_collection_service(collection_id, user_id)
    # Validate everything before anything is written to disk.
    validated: list[tuple[str, str, bytes]] = []
    for upload in files:
        content = await read_limited(upload)
        safe_name, content_type = validate_upload(upload.filename, content)
        validated.append((safe_name, content_type, content))
    results = []
    for safe_name, content_type, content in validated:
        file_id = str(uuid.uuid4())
        folder = Path(cfg.UPLOAD_DIR) / collection_id
        folder.mkdir(parents=True, exist_ok=True)
        # uuid name on disk; the original (sanitized) filename lives only in the database
        path = folder / f"{file_id}{Path(safe_name).suffix.lower()}"
        path.write_bytes(content)

        async with get_db() as session:
            session.add(CollectionFile(
                id=file_id, collection_id=collection_id, filename=safe_name,
                content_type=content_type, size=len(content), status="indexing",
            ))
        results.append(await _index_file(collection_id, file_id, safe_name, path))
    return results
