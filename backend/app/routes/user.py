from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.middleware import response_envelope
from app.model import Consultation, Notification, User, UserProfile
from app.routes.deps import get_current_user, require_roles
from app.schema import HealthProfileUpdateIn, ProfileUpdateIn
from app.service import (
    ensure_user_profile,
    latest_ai,
    latest_reply,
    log_operation,
    paginate,
    serialize_account,
    serialize_health,
    serialize_profile,
)


router = APIRouter()


@router.get("/profile")
def get_profile(
    request: Request,
    user: User = Depends(require_roles("USER", "DOCTOR", "ADMIN")),
    db: Session = Depends(get_db),
) -> dict:
    profile, health = ensure_user_profile(db, user.id)
    return response_envelope(
        request,
        {
            "account": serialize_account(user),
            "profile": serialize_profile(user, profile),
            "health_profile": serialize_health(health),
        },
    )


@router.put("/profile")
def update_profile(
    payload: ProfileUpdateIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    profile, _ = ensure_user_profile(db, user.id)
    for field in ["real_name", "gender", "age", "city", "occupation", "emergency_contact", "emergency_phone", "remark"]:
        value = getattr(payload, field)
        if value is not None:
            setattr(profile, field, value)
    if payload.birthday:
        try:
            profile.birthday = date.fromisoformat(payload.birthday)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="生日格式需为 YYYY-MM-DD") from exc
    if payload.avatar_url is not None:
        user.avatar_url = payload.avatar_url
    profile.updated_at = datetime.utcnow()
    user.updated_at = datetime.utcnow()
    log_operation(db, user.id, user.role_type, "USER", "UPDATE_PROFILE", str(user.id), "更新个人资料", request.client.host if request.client else None)
    db.commit()
    return response_envelope(request, {"profile": serialize_profile(user, profile)}, "保存成功")


@router.get("/health-profile")
def get_health_profile(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    _, health = ensure_user_profile(db, user.id)
    return response_envelope(request, serialize_health(health))


@router.put("/health-profile")
def update_health_profile(
    payload: HealthProfileUpdateIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    profile, health = ensure_user_profile(db, user.id)
    if not health:
        from app.model import HealthProfile

        health = HealthProfile(user_profile_id=profile.id, updated_at=datetime.utcnow())
        db.add(health)
        db.flush()
    for field in [
        "allergy_history",
        "past_medical_history",
        "medication_history",
        "skin_type",
        "skin_sensitivity",
        "sleep_pattern",
        "diet_preference",
        "special_notes",
    ]:
        value = getattr(payload, field)
        if value is not None:
            setattr(health, field, value)
    health.updated_at = datetime.utcnow()
    log_operation(db, user.id, user.role_type, "USER", "UPDATE_HEALTH", str(user.id), "更新健康档案", request.client.host if request.client else None)
    db.commit()
    return response_envelope(request, serialize_health(health), "保存成功")


@router.get("/notifications")
def notifications(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    rows = db.execute(select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc())).scalars().all()
    data = paginate(
        [
            {
                "notification_id": row.id,
                "title": row.title,
                "content": row.content,
                "notification_type": row.notification_type,
                "related_business_type": row.related_business_type,
                "related_business_id": row.related_business_id,
                "read_flag": row.read_flag,
                "created_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for row in rows
        ],
        page,
        page_size,
    )
    return response_envelope(request, data)


@router.get("/dashboard")
def user_dashboard(request: Request, user: User = Depends(require_roles("USER")), db: Session = Depends(get_db)) -> dict:
    profile, health = ensure_user_profile(db, user.id)
    cases = db.execute(select(Consultation).where(Consultation.user_id == user.id).order_by(Consultation.created_at.desc())).scalars().all()
    recent = []
    for case in cases[:3]:
        recent.append(
            {
                "case_id": case.id,
                "case_no": case.case_no,
                "summary_title": case.summary_title,
                "status": case.status,
                "risk_level": case.risk_level,
                "ai_result": latest_ai(db, case.id).risk_level if latest_ai(db, case.id) else None,
                "doctor_replied": bool(latest_reply(db, case.id)),
                "submitted_at": case.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if case.submitted_at else None,
            }
        )
    unread = db.scalar(select(func.count(Notification.id)).where(Notification.user_id == user.id, Notification.read_flag == 0)) or 0
    active = next((case for case in cases if case.status in {"WAIT_DOCTOR", "AI_DONE", "DOCTOR_REPLIED"}), None)
    return response_envelope(
        request,
        {
            "account": serialize_account(user),
            "profile": serialize_profile(user, profile),
            "health_profile": serialize_health(health),
            "summary": {
                "consultation_total": len(cases),
                "waiting_total": len([case for case in cases if case.status in {"WAIT_DOCTOR", "PENDING_AI"}]),
                "doctor_replied_total": len([case for case in cases if case.status == "DOCTOR_REPLIED"]),
                "unread_notifications": unread,
            },
            "current_focus": {
                "case_id": active.id,
                "case_no": active.case_no,
                "status": active.status,
                "risk_level": active.risk_level,
                "summary_title": active.summary_title,
            }
            if active
            else None,
            "recent_cases": recent,
        },
    )


@router.get("/patients/{user_id}")
def patient_profile_for_doctor(
    user_id: int,
    request: Request,
    user: User = Depends(require_roles("DOCTOR", "ADMIN")),
    db: Session = Depends(get_db),
) -> dict:
    patient = db.scalar(select(User).where(User.id == user_id, User.role_type == "USER", User.is_deleted == 0))
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == patient.id))
    _, health = ensure_user_profile(db, patient.id)
    return response_envelope(
        request,
        {
            "account": serialize_account(patient),
            "profile": serialize_profile(patient, profile),
            "health_profile": serialize_health(health),
        },
    )
