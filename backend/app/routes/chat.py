from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.chat_graph import DEFAULT_SESSION_TITLE, TextChatService
from app.chat_store import ensure_chat_tables, load_session_last_message, serialize_chat_message
from app.db import get_db
from app.middleware import response_envelope
from app.model import ChatMessage, ChatSession, ToolCallLog, User
from app.routes.deps import get_current_user
from app.schema import ChatMessageCreateIn, ChatSessionCreateIn
from app.service import log_operation


router = APIRouter()


def _ensure_user_chat_access(user: User) -> None:
    if user.role_type != "USER":
        raise HTTPException(status_code=403, detail="当前账号不能使用知识问答")


def _load_session_or_404(db: Session, session_id: int, user_id: int) -> ChatSession:
    session = db.scalar(select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id))
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    return session


@router.post("/sessions")
def create_session(
    payload: ChatSessionCreateIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    _ensure_user_chat_access(user)
    ensure_chat_tables(db)

    now = datetime.utcnow()
    session = ChatSession(
        user_id=user.id,
        title=(payload.title or DEFAULT_SESSION_TITLE).strip()[:120] or DEFAULT_SESSION_TITLE,
        created_at=now,
        updated_at=now,
    )
    db.add(session)
    db.flush()
    log_operation(db, user.id, user.role_type, "CHAT", "CREATE_SESSION", str(session.id), "创建知识问答会话", request.client.host if request.client else None)
    db.commit()

    return response_envelope(
        request,
        {
            "session_id": session.id,
            "title": session.title,
            "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "创建成功",
    )


@router.get("/sessions")
def list_sessions(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    _ensure_user_chat_access(user)
    ensure_chat_tables(db)

    sessions = (
        db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user.id)
            .order_by(ChatSession.updated_at.desc(), ChatSession.id.desc())
        )
        .scalars()
        .all()
    )
    data = {
        "items": [
            {
                "session_id": session.id,
                "title": session.title,
                "last_message": load_session_last_message(db, session.id),
                "updated_at": session.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for session in sessions
        ]
    }
    return response_envelope(request, data)


@router.get("/sessions/{session_id}/messages")
def session_messages(
    session_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    _ensure_user_chat_access(user)
    ensure_chat_tables(db)
    session = _load_session_or_404(db, session_id, user.id)

    rows = (
        db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session.id)
            .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
        )
        .scalars()
        .all()
    )
    return response_envelope(
        request,
        {
            "session_id": session.id,
            "title": session.title,
            "messages": [serialize_chat_message(row) for row in rows],
        },
    )


@router.post("/sessions/{session_id}/messages")
def send_message(
    session_id: int,
    payload: ChatMessageCreateIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    _ensure_user_chat_access(user)
    ensure_chat_tables(db)
    session = _load_session_or_404(db, session_id, user.id)
    content = payload.message.strip()
    if not content:
        raise HTTPException(status_code=400, detail="消息不能为空")

    service = TextChatService(db, user.id)
    state = service.run(session, content)
    log_operation(
        db,
        user.id,
        user.role_type,
        "CHAT",
        "SEND_MESSAGE",
        str(session.id),
        f"发送知识问答消息，意图={state.get('intent') or 'UNKNOWN'}",
        request.client.host if request.client else None,
    )
    db.commit()

    return response_envelope(
        request,
        {
            "message_id": state["saved_message_id"],
            "answer": state["final_answer"],
            "intent": state.get("intent"),
            "used_tool": bool(state.get("used_tool")),
            "tool_name": state.get("tool_name") if state.get("used_tool") else None,
            "sources": state.get("sources", []),
            "created_at": state["created_at"],
        },
        "回答成功",
    )


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    _ensure_user_chat_access(user)
    ensure_chat_tables(db)
    session = _load_session_or_404(db, session_id, user.id)

    db.execute(delete(ToolCallLog).where(ToolCallLog.session_id == session.id))
    db.execute(delete(ChatMessage).where(ChatMessage.session_id == session.id))
    db.delete(session)
    log_operation(
        db,
        user.id,
        user.role_type,
        "CHAT",
        "DELETE_SESSION",
        str(session.id),
        "删除知识问答会话",
        request.client.host if request.client else None,
    )
    db.commit()
    return response_envelope(request, {"session_id": session_id}, "删除成功")
