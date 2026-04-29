from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.middleware import response_envelope
from app.model import Announcement, User
from app.routes.deps import get_current_user
from app.service import log_operation


router = APIRouter()
settings = get_settings()
MAX_IMAGE_SIZE = 7 * 1024 * 1024
ALLOWED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.get("/announcements")
def list_announcements(request: Request, db: Session = Depends(get_db)) -> dict:
    rows = db.execute(
        select(Announcement)
        .where(Announcement.status == 1)
        .order_by(Announcement.published_at.desc(), Announcement.id.desc())
    ).scalars().all()
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
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=400, detail="仅支持 JPG、PNG、WEBP 图片")
    if file.content_type and file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="图片类型不合法，请上传 JPG、PNG 或 WEBP")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="上传图片内容为空")
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="图片大小不能超过 7MB")

    target_dir = settings.upload_path / scene
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{user.id}-{abs(hash(file.filename)) % 99999}{suffix}"
    target_file = target_dir / filename
    target_file.write_bytes(content)

    file_url = f"{settings.base_url}/uploads/{scene}/{filename}"
    log_operation(
        db,
        user.id,
        user.role_type,
        "FILE",
        "UPLOAD_IMAGE",
        filename,
        f"上传图片 {file.filename}",
        request.client.host if request.client else None,
    )
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

