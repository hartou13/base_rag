import uuid

from fastapi import HTTPException
from sqlalchemy import delete, func, select

from src.database.mysql_connector import get_db
from src.sessions.dto.session_dto import (
    CreateSessionDto,
    MessageDto,
    SessionDetailDto,
    SessionDto,
    UpdateSessionDto,
)
from src.sessions.models.chat_message import ChatMessage
from src.sessions.models.chat_session import ChatSession


def _to_dto(s: ChatSession) -> SessionDto:
    return SessionDto(id=s.id, title=s.title, created_at=s.created_at, updated_at=s.updated_at)


def _message_dto(m: ChatMessage) -> MessageDto:
    return MessageDto(id=m.id, role=m.role, content=m.content, created_at=m.created_at)


async def get_owned_session_service(session_id: str, user_id: str) -> ChatSession:
    async with get_db() as session:
        result = await session.execute(
            select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)
        )
        chat_session = result.scalar_one_or_none()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return chat_session


async def create_session_service(user_id: str, data: CreateSessionDto) -> SessionDto:
    async with get_db() as session:
        chat_session = ChatSession(id=str(uuid.uuid4()), user_id=user_id, title=data.title or "New chat")
        session.add(chat_session)
        await session.flush()
        await session.refresh(chat_session)
        return _to_dto(chat_session)


async def list_sessions_service(user_id: str) -> list[SessionDto]:
    async with get_db() as session:
        result = await session.execute(
            select(ChatSession).where(ChatSession.user_id == user_id).order_by(ChatSession.updated_at.desc())
        )
        return [_to_dto(s) for s in result.scalars().all()]


async def get_session_service(session_id: str, user_id: str) -> SessionDetailDto:
    chat_session = await get_owned_session_service(session_id, user_id)
    async with get_db() as session:
        result = await session.execute(
            select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at, ChatMessage.id)
        )
        messages = [_message_dto(m) for m in result.scalars().all()]
    return SessionDetailDto(**_to_dto(chat_session).model_dump(), messages=messages)


async def update_session_service(session_id: str, user_id: str, data: UpdateSessionDto) -> SessionDto:
    await get_owned_session_service(session_id, user_id)
    async with get_db() as session:
        chat_session = await session.get(ChatSession, session_id)
        chat_session.title = data.title
        await session.flush()
        await session.refresh(chat_session)
        return _to_dto(chat_session)


async def delete_session_service(session_id: str, user_id: str):
    await get_owned_session_service(session_id, user_id)
    async with get_db() as session:
        await session.execute(delete(ChatMessage).where(ChatMessage.session_id == session_id))
        await session.execute(delete(ChatSession).where(ChatSession.id == session_id))
    return {"message": "Session deleted"}


async def get_recent_messages_service(session_id: str, limit: int) -> list[dict]:
    """Last `limit` messages as {"role", "content"} dicts, oldest first (ready for the model)."""
    async with get_db() as session:
        result = await session.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
            .limit(limit)
        )
        rows = result.scalars().all()
    return [{"role": m.role, "content": m.content} for m in reversed(rows)]


async def add_messages_service(session_id: str, messages: list[tuple[str, str]]):
    """Appends (role, content) pairs in order and bumps the session's updated_at."""
    async with get_db() as session:
        for role, content in messages:
            session.add(ChatMessage(id=str(uuid.uuid4()), session_id=session_id, role=role, content=content))
            await session.flush()  # separate inserts keep created_at ordered
        await session.execute(
            ChatSession.__table__.update().where(ChatSession.id == session_id).values(updated_at=func.now())
        )
