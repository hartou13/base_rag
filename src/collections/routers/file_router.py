from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from src.collections.dto.collection_dto import CollectionFileDto
from src.collections.services.collection_service import (
    delete_file_service,
    get_file_content_service,
    reindex_file_service,
)
from src.users.services.user_service import get_current_user

router = APIRouter(
    prefix="/files",
    tags=["files"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{file_id}/content")
async def get_file_content(file_id: str, download: bool = False, current_user: str = Depends(get_current_user)):
    """Return the original uploaded file. `?download=true` forces a download instead of inline display."""
    path, db_file = await get_file_content_service(file_id, current_user)
    return FileResponse(
        path,
        media_type=db_file.content_type or "application/octet-stream",
        filename=db_file.filename,
        content_disposition_type="attachment" if download else "inline",
    )


@router.post("/{file_id}/reindex", response_model=CollectionFileDto)
async def reindex_file(file_id: str, current_user: str = Depends(get_current_user)):
    return await reindex_file_service(file_id, current_user)


@router.delete("/{file_id}")
async def delete_file(file_id: str, current_user: str = Depends(get_current_user)):
    return await delete_file_service(file_id, current_user)
