from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.model import ChatMessage, ChatSession, ToolCallLog


_READY_BINDS: set[int] = set()


def ensure_chat_tables(db: Session) -> None:
    bind = db.get_bind()
    bind_key = id(bind)
    if bind_key in _READY_BINDS:
        return

    for table in (ChatSession.__table__, ChatMessage.__table__, ToolCallLog.__table__):
        table.create(bind=bind, checkfirst=True)

    _READY_BINDS.add(bind_key)


def build_session_title(message: str, fallback: str = "新的对话") -> str:
    cleaned = " ".join(message.split())
    if not cleaned:
        return fallback
    return cleaned[:20]


def parse_sources(raw: str | None) -> list[dict]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def serialize_chat_message(message: ChatMessage) -> dict:
    return {
        "message_id": message.id,
        "role": message.role,
        "content": message.content,
        "intent": message.intent,
        "used_tool": bool(message.used_tool),
        "tool_name": message.tool_name,
        "sources": parse_sources(message.sources_json),
        "model_name": message.model_name,
        "created_at": message.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


def load_session_last_message(db: Session, session_id: int) -> str | None:
    row = db.scalar(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
    )
    return row.content if row else None


def touch_session(session: ChatSession, at: datetime | None = None) -> None:
    session.updated_at = at or datetime.utcnow()
