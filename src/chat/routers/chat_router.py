from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from src.chat.dto.chat_dto import ChatRequestDto
from src.chat.services.chat_service import chat_service
from src.users.services.user_service import get_current_user

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)


@router.post("")
async def chat(data: ChatRequestDto, current_user: str = Depends(get_current_user)):
    """Streams Server-Sent Events: `sources`, then `token` pieces, then `done` (or `error`)."""
    stream = await chat_service(data, current_user)
    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
