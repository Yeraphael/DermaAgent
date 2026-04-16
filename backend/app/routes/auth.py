from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.middleware import response_envelope
from app.model import Admin, Doctor, User
from app.routes.deps import get_current_user
from app.schema import LoginIn, PasswordChangeIn, RegisterIn
from app.service import ensure_user_profile, log_operation, serialize_account, serialize_health, serialize_profile
from app.utils import create_access_token, hash_password, verify_password


router = APIRouter()


@router.post("/register")
def register(payload: RegisterIn, request: Request, db: Session = Depends(get_db)) -> dict:
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="两次输入的密码不一致")
    if payload.role_type not in {"USER", "DOCTOR"}:
        raise HTTPException(status_code=400, detail="仅支持注册用户或医生账号")
    exists = db.scalar(select(User).where(User.username == payload.username, User.is_deleted == 0))
    if exists:
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        role_type=payload.role_type,
        phone=payload.phone,
        email=payload.email,
        status=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        is_deleted=0,
    )
    db.add(user)
    db.flush()
    profile, health = ensure_user_profile(db, user.id)
    if payload.role_type == "DOCTOR":
        db.add(
            Doctor(
                user_id=user.id,
                doctor_name=payload.username,
                department="皮肤科",
                title_name="待认证医生",
                hospital_name="待完善",
                specialty="皮炎湿疹、痤疮、真菌感染",
                intro="请在管理端完善执业信息后开始接诊。",
                license_no=f"TMP-{user.id:06d}",
                audit_status="PENDING",
                service_status=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )
    db.commit()
    log_operation(db, user.id, user.role_type, "AUTH", "REGISTER", str(user.id), "新账号注册", request.client.host if request.client else None)
    db.commit()
    return response_envelope(
        request,
        {
            "account": serialize_account(user),
            "profile": serialize_profile(user, profile),
            "health_profile": serialize_health(health),
        },
        "注册成功",
    )


@router.post("/login")
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)) -> dict:
    user = db.scalar(select(User).where(User.username == payload.username, User.is_deleted == 0))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    if user.status != 1:
        raise HTTPException(status_code=403, detail="账号已被停用")
    user.last_login_at = datetime.utcnow()
    user.updated_at = datetime.utcnow()
    token = create_access_token(str(user.id), user.role_type)
    profile, health = ensure_user_profile(db, user.id)
    doctor = db.scalar(select(Doctor).where(Doctor.user_id == user.id)) if user.role_type == "DOCTOR" else None
    admin = db.scalar(select(Admin).where(Admin.user_id == user.id)) if user.role_type == "ADMIN" else None
    log_operation(db, user.id, user.role_type, "AUTH", "LOGIN", str(user.id), "账号登录", request.client.host if request.client else None)
    db.commit()
    return response_envelope(
        request,
        {
            "access_token": token,
            "token_type": "Bearer",
            "account": serialize_account(user),
            "profile": serialize_profile(user, profile),
            "health_profile": serialize_health(health),
            "doctor_info": {
                "doctor_id": doctor.id,
                "doctor_name": doctor.doctor_name,
                "department": doctor.department,
                "title_name": doctor.title_name,
                "audit_status": doctor.audit_status,
                "service_status": doctor.service_status,
            }
            if doctor
            else None,
            "admin_info": {
                "admin_id": admin.id,
                "admin_name": admin.admin_name,
                "job_title": admin.job_title,
                "permissions_summary": admin.permissions_summary,
            }
            if admin
            else None,
        },
        "登录成功",
    )


@router.get("/me")
def me(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    profile, health = ensure_user_profile(db, user.id)
    doctor = db.scalar(select(Doctor).where(Doctor.user_id == user.id)) if user.role_type == "DOCTOR" else None
    admin = db.scalar(select(Admin).where(Admin.user_id == user.id)) if user.role_type == "ADMIN" else None
    return response_envelope(
        request,
        {
            "account": serialize_account(user),
            "profile": serialize_profile(user, profile),
            "health_profile": serialize_health(health),
            "doctor_info": {
                "doctor_id": doctor.id,
                "doctor_name": doctor.doctor_name,
                "department": doctor.department,
                "title_name": doctor.title_name,
                "hospital_name": doctor.hospital_name,
                "specialty": doctor.specialty,
                "audit_status": doctor.audit_status,
                "service_status": doctor.service_status,
            }
            if doctor
            else None,
            "admin_info": {
                "admin_id": admin.id,
                "admin_name": admin.admin_name,
                "job_title": admin.job_title,
                "permissions_summary": admin.permissions_summary,
            }
            if admin
            else None,
        },
    )


@router.put("/password")
def change_password(
    payload: PasswordChangeIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="两次输入的新密码不一致")
    if not verify_password(payload.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    user.password_hash = hash_password(payload.new_password)
    user.updated_at = datetime.utcnow()
    log_operation(db, user.id, user.role_type, "AUTH", "CHANGE_PASSWORD", str(user.id), "修改密码", request.client.host if request.client else None)
    db.commit()
    return response_envelope(request, {"success": True}, "密码修改成功")


@router.post("/logout")
def logout(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    log_operation(db, user.id, user.role_type, "AUTH", "LOGOUT", str(user.id), "退出登录", request.client.host if request.client else None)
    db.commit()
    return response_envelope(request, {"success": True}, "退出成功")
