from typing import List

from fastapi import APIRouter, Depends

from src.sessions.dto.session_dto import CreateSessionDto, SessionDetailDto, SessionDto, UpdateSessionDto
from src.sessions.services.session_service import (
    create_session_service,
    delete_session_service,
    get_session_service,
    list_sessions_service,
    update_session_service,
)
from src.users.services.user_service import get_current_user

router = APIRouter(
    prefix="/sessions",
    tags=["sessions"],
    responses={404: {"description": "Not found"}},
)


@router.post("", response_model=SessionDto)
async def create_session(data: CreateSessionDto, current_user: str = Depends(get_current_user)):
    return await create_session_service(current_user, data)


@router.get("", response_model=List[SessionDto])
async def list_sessions(current_user: str = Depends(get_current_user)):
    return await list_sessions_service(current_user)


@router.get("/{session_id}", response_model=SessionDetailDto)
async def get_session(session_id: str, current_user: str = Depends(get_current_user)):
    return await get_session_service(session_id, current_user)


@router.put("/{session_id}", response_model=SessionDto)
async def update_session(session_id: str, data: UpdateSessionDto, current_user: str = Depends(get_current_user)):
    return await update_session_service(session_id, current_user, data)


@router.delete("/{session_id}")
async def delete_session(session_id: str, current_user: str = Depends(get_current_user)):
    return await delete_session_service(session_id, current_user)
