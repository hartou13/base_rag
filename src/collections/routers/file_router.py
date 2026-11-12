from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from src.collections.dto.collection_dto import CollectionFileDto
from src.collections.services.collection_service import (
    delete_file_service,
    get_file_content_service,
    get_owned_file_service,
    reindex_file_service,
)
from src.collections.services.file_token_service import sign, verify
from src.users.services.user_service import get_current_user

router = APIRouter(
    prefix="/files",
    tags=["files"],
    responses={404: {"description": "Not found"}},
)

_FILE_HEADERS = {"X-Content-Type-Options": "nosniff", "Content-Security-Policy": "sandbox; default-src 'none'"}


@router.get("/{file_id}/download")
async def get_download_url(file_id: str, current_user: str = Depends(get_current_user)):
    """Return a short-lived signed URL (HMAC over file id, user id and expiry) for downloading the file."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Token is missing")
    await get_owned_file_service(file_id, current_user)  # owner check
    uid, exp, sig = sign(file_id, current_user)
    return {
        "url": f"/files/{file_id}/content?uid={uid}&exp={exp}&sig={sig}",
        "expires_at": datetime.fromtimestamp(exp, tz=timezone.utc).isoformat(),
    }


@router.get("/{file_id}/content")
async def get_file_content(
    file_id: str,
    download: bool = False,
    uid: Optional[str] = None,
    exp: Optional[int] = None,
    sig: Optional[str] = None,
    current_user: Optional[str] = Depends(get_current_user),
):
    """Stream the uploaded file. Either a Bearer token (owner), or a valid signed URL from /download.
    A signed request is public to the middleware, so signature, expiry and owner are all checked here."""
    if sig is not None:
        if not uid or exp is None or not verify(file_id, uid, exp, sig):
            raise HTTPException(status_code=403, detail="Forbidden")
        user_id, download = uid, True
    elif current_user:
        user_id = current_user
    else:
        raise HTTPException(status_code=401, detail="Token is missing")
    try:
        path, db_file = await get_file_content_service(file_id, user_id)  # owner check
    except HTTPException as e:
        if sig is not None:
            raise HTTPException(status_code=403, detail="Forbidden") from e
        raise
    media_type = db_file.content_type or "application/octet-stream"
    inline_ok = media_type == "application/pdf" and not download
    return FileResponse(
        path,
        media_type=media_type,
        filename=db_file.filename,
        content_disposition_type="inline" if inline_ok else "attachment",
        headers=_FILE_HEADERS,
    )


@router.post("/{file_id}/reindex", response_model=CollectionFileDto)
async def reindex_file(file_id: str, current_user: str = Depends(get_current_user)):
    return await reindex_file_service(file_id, current_user)


@router.delete("/{file_id}")
async def delete_file(file_id: str, current_user: str = Depends(get_current_user)):
    return await delete_file_service(file_id, current_user)
