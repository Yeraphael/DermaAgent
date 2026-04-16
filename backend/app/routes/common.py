from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.middleware import response_envelope
from app.model import Announcement, QARecord, User
from app.rag import rag_engine
from app.routes.deps import get_current_user
from app.schema import QuestionIn
from app.service import log_operation


router = APIRouter()
settings = get_settings()


@router.get("/announcements")
def list_announcements(request: Request, db: Session = Depends(get_db)) -> dict:
    rows = db.execute(select(Announcement).where(Announcement.status == 1).order_by(Announcement.published_at.desc(), Announcement.id.desc())).scalars().all()
    data = [
        {
            "announcement_id": row.id,
            "title": row.title,
            "content": row.content,
            "publish_scope": row.publish_scope,
            "published_at": row.published_at.strftime("%Y-%m-%d %H:%M:%S") if row.published_at else None,
        }
        for row in rows
    ]
    return response_envelope(request, data)


@router.post("/files/upload-image")
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    scene: str = Form(default="consultation"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="缺少文件名")
    suffix = ""
    if "." in file.filename:
        suffix = "." + file.filename.rsplit(".", 1)[-1].lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(status_code=400, detail="仅支持 jpg/jpeg/png/webp 图片")
    target_dir = settings.upload_path / scene
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{user.id}-{abs(hash(file.filename)) % 99999}{suffix}"
    target_file = target_dir / filename
    content = await file.read()
    target_file.write_bytes(content)
    file_url = f"{settings.base_url}/uploads/{scene}/{filename}"
    log_operation(db, user.id, user.role_type, "FILE", "UPLOAD_IMAGE", filename, f"上传图片 {file.filename}", request.client.host if request.client else None)
    db.commit()
    return response_envelope(
        request,
        {
            "file_name": file.filename,
            "stored_name": filename,
            "file_size": len(content),
            "file_type": file.content_type,
            "file_url": file_url,
        },
        "上传成功",
    )


@router.post("/rag/qa")
def ask_question(
    payload: QuestionIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    answer, refs, risk_hint = rag_engine.answer(db, payload.question)
    record = QARecord(
        user_id=user.id,
        related_consultation_id=payload.related_case_id,
        question_text=payload.question,
        answer_text=answer,
        references_json=rag_engine.dump_refs(refs),
        risk_hint=risk_hint,
        answer_status="SUCCESS",
        model_name="mock-rag" if settings.rag_mode.lower() == "mock" else settings.qwen_text_model,
        created_at=datetime.utcnow(),
    )
    db.add(record)
    log_operation(db, user.id, user.role_type, "RAG", "QA", str(record.id or ""), "提交知识问答", request.client.host if request.client else None)
    db.commit()
    return response_envelope(
        request,
        {
            "qa_id": record.id,
            "question": payload.question,
            "answer": answer,
            "references": refs,
            "risk_hint": risk_hint,
            "mode": settings.rag_mode,
        },
        "回答成功",
    )


@router.get("/rag/qa/history")
def qa_history(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    rows = db.execute(select(QARecord).where(QARecord.user_id == user.id).order_by(QARecord.created_at.desc())).scalars().all()
    start = (page - 1) * page_size
    items = rows[start : start + page_size]
    return response_envelope(
        request,
        {
            "list": [
                {
                    "qa_id": row.id,
                    "question": row.question_text,
                    "answer": row.answer_text,
                    "risk_hint": row.risk_hint,
                    "created_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for row in items
            ],
            "total": len(rows),
            "page": page,
            "page_size": page_size,
        },
    )


@router.get("/rag/qa/{qa_id}")
def qa_detail(
    qa_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    row = db.scalar(select(QARecord).where(QARecord.id == qa_id, QARecord.user_id == user.id))
    if not row:
        raise HTTPException(status_code=404, detail="记录不存在")
    return response_envelope(
        request,
        {
            "qa_id": row.id,
            "question": row.question_text,
            "answer": row.answer_text,
            "references": row.references_json,
            "risk_hint": row.risk_hint,
            "status": row.answer_status,
            "created_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        },
    )
