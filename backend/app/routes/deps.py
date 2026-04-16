from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.model import User
from app.utils import decode_token


def _unauthorized(detail: str = "未登录或登录已过期") -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise _unauthorized()
    token = authorization.replace("Bearer ", "", 1).strip()
    try:
        payload = decode_token(token)
    except Exception as exc:  # noqa: BLE001
        raise _unauthorized("令牌校验失败") from exc
    user_id = payload.get("sub")
    if not user_id:
        raise _unauthorized("令牌缺少主体信息")
    user = db.scalar(select(User).where(User.id == int(user_id), User.is_deleted == 0))
    if not user or user.status != 1:
        raise _unauthorized("账号不可用")
    return user


def require_roles(*roles: str) -> Callable[[User], User]:
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role_type not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问当前资源")
        return user

    return dependency


def query_pagination(page: int = 1, page_size: int = 10) -> dict[str, Any]:
    page = max(page, 1)
    page_size = max(min(page_size, 50), 1)
    return {"page": page, "page_size": page_size}

