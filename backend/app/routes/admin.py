from __future__ import annotations

from collections import Counter
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.chat_store import ensure_chat_tables
from app.db import get_db
from app.middleware import response_envelope
from app.model import (
    AIAnalysisRecord,
    Admin,
    Announcement,
    ChatMessage,
    ChatSession,
    Consultation,
    Doctor,
    OperationLog,
    StatisticsSnapshot,
    SystemConfig,
    ToolCallLog,
    User,
    UserProfile,
)
from app.routes.deps import require_roles
from app.schema import AnnouncementIn, AuditUpdateIn, ConfigUpdateIn, StatusUpdateIn
from app.service import build_consultation_detail, log_operation, serialize_account, serialize_profile


router = APIRouter()


def _current_admin(user: User, db: Session) -> Admin:
    admin = db.scalar(select(Admin).where(Admin.user_id == user.id))
    if not admin:
        raise HTTPException(status_code=404, detail="管理员资料不存在")
    return admin


@router.get("/users")
def users(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    keyword: str | None = Query(default=None),
    status: int | None = Query(default=None),
    user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db),
) -> dict:
    _current_admin(user, db)
    rows = db.execute(select(User).where(User.role_type == "USER", User.is_deleted == 0).order_by(User.created_at.desc())).scalars().all()
    if keyword:
        rows = [row for row in rows if keyword.lower() in f"{row.username} {row.phone or ''} {row.email or ''}".lower()]
    if status is not None:
        rows = [row for row in rows if row.status == status]
    profiles = {profile.user_id: profile for profile in db.execute(select(UserProfile)).scalars().all()}
    start = (page - 1) * page_size
    items = rows[start : start + page_size]
    return response_envelope(
        request,
        {
            "list": [
                {
                    "account": serialize_account(row),
                    "profile": serialize_profile(row, profiles.get(row.id)),
                }
                for row in items
            ],
            "total": len(rows),
            "page": page,
            "page_size": page_size,
        },
    )


@router.get("/users/{user_id}")
def user_detail(user_id: int, request: Request, user: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict:
    _current_admin(user, db)
    target = db.scalar(select(User).where(User.id == user_id, User.role_type == "USER", User.is_deleted == 0))
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")
    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == target.id))
    consultations = db.execute(select(Consultation).where(Consultation.user_id == target.id).order_by(Consultation.created_at.desc())).scalars().all()
    return response_envelope(
        request,
        {
            "account": serialize_account(target),
            "profile": serialize_profile(target, profile),
            "recent_consultations": [
                {
                    "case_id": row.id,
                    "case_no": row.case_no,
                    "summary_title": row.summary_title,
                    "status": row.status,
                    "risk_level": row.risk_level,
                    "submitted_at": row.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if row.submitted_at else None,
                }
                for row in consultations[:10]
            ],
        },
    )


@router.put("/users/{user_id}/status")
def update_user_status(
    user_id: int,
    payload: StatusUpdateIn,
    request: Request,
    user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db),
) -> dict:
    _current_admin(user, db)
    target = db.scalar(select(User).where(User.id == user_id, User.role_type == "USER", User.is_deleted == 0))
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")
    target.status = payload.status
    target.updated_at = datetime.utcnow()
    log_operation(db, user.id, user.role_type, "ADMIN", "UPDATE_USER_STATUS", str(target.id), f"更新用户状态为 {payload.status}", request.client.host if request.client else None)
    db.commit()
    return response_envelope(request, {"user_id": target.id, "status": target.status}, "更新成功")


@router.get("/doctors")
def doctors(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    keyword: str | None = Query(default=None),
    audit_status: str | None = Query(default=None),
    user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db),
) -> dict:
    _current_admin(user, db)
    rows = db.execute(select(Doctor).order_by(Doctor.created_at.desc())).scalars().all()
    if keyword:
        rows = [row for row in rows if keyword.lower() in f"{row.doctor_name} {row.department or ''} {row.hospital_name or ''}".lower()]
    if audit_status:
        rows = [row for row in rows if row.audit_status == audit_status]
    accounts = {row.id: row for row in db.execute(select(User)).scalars().all()}
    start = (page - 1) * page_size
    items = rows[start : start + page_size]
    return response_envelope(
        request,
        {
            "list": [
                {
                    "doctor_id": row.id,
                    "account": serialize_account(accounts.get(row.user_id)),
                    "doctor_name": row.doctor_name,
                    "department": row.department,
                    "title_name": row.title_name,
                    "hospital_name": row.hospital_name,
                    "specialty": row.specialty,
                    "audit_status": row.audit_status,
                    "audit_remark": row.audit_remark,
                    "service_status": row.service_status,
                    "created_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for row in items
            ],
            "total": len(rows),
            "page": page,
            "page_size": page_size,
        },
    )


@router.get("/doctors/{doctor_id}")
def doctor_detail(doctor_id: int, request: Request, user: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict:
    _current_admin(user, db)
    doctor = db.scalar(select(Doctor).where(Doctor.id == doctor_id))
    if not doctor:
        raise HTTPException(status_code=404, detail="医生不存在")
    account = db.scalar(select(User).where(User.id == doctor.user_id))
    return response_envelope(
        request,
        {
            "account": serialize_account(account),
            "doctor": {
                "doctor_id": doctor.id,
                "doctor_name": doctor.doctor_name,
                "department": doctor.department,
                "title_name": doctor.title_name,
                "hospital_name": doctor.hospital_name,
                "specialty": doctor.specialty,
                "intro": doctor.intro,
                "license_no": doctor.license_no,
                "audit_status": doctor.audit_status,
                "audit_remark": doctor.audit_remark,
                "service_status": doctor.service_status,
            },
        },
    )


@router.put("/doctors/{doctor_id}/audit")
def doctor_audit(
    doctor_id: int,
    payload: AuditUpdateIn,
    request: Request,
    user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db),
) -> dict:
    _current_admin(user, db)
    doctor = db.scalar(select(Doctor).where(Doctor.id == doctor_id))
    if not doctor:
        raise HTTPException(status_code=404, detail="医生不存在")
    doctor.audit_status = payload.audit_status
    doctor.audit_remark = payload.audit_remark
    doctor.service_status = 1 if payload.audit_status == "APPROVED" else 0
    doctor.updated_at = datetime.utcnow()
    log_operation(db, user.id, user.role_type, "ADMIN", "DOCTOR_AUDIT", str(doctor.id), f"医生审核结果 {payload.audit_status}", request.client.host if request.client else None)
    db.commit()
    return response_envelope(request, {"doctor_id": doctor.id, "audit_status": doctor.audit_status}, "审核成功")


@router.put("/doctors/{doctor_id}/status")
def doctor_status(
    doctor_id: int,
    payload: StatusUpdateIn,
    request: Request,
    user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db),
) -> dict:
    _current_admin(user, db)
    doctor = db.scalar(select(Doctor).where(Doctor.id == doctor_id))
    if not doctor:
        raise HTTPException(status_code=404, detail="医生不存在")
    doctor.service_status = payload.status
    doctor.updated_at = datetime.utcnow()
    log_operation(db, user.id, user.role_type, "ADMIN", "DOCTOR_STATUS", str(doctor.id), f"医生服务状态 {payload.status}", request.client.host if request.client else None)
    db.commit()
    return response_envelope(request, {"doctor_id": doctor.id, "service_status": doctor.service_status}, "更新成功")


@router.get("/consultations")
def consultations(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    status: str | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db),
) -> dict:
    _current_admin(user, db)
    rows = db.execute(select(Consultation).where(Consultation.is_deleted == 0).order_by(Consultation.created_at.desc())).scalars().all()
    if status:
        rows = [row for row in rows if row.status == status]
    if risk_level:
        rows = [row for row in rows if row.risk_level == risk_level]
    start = (page - 1) * page_size
    items = rows[start : start + page_size]
    return response_envelope(
        request,
        {
            "list": [build_consultation_detail(db, row, include_patient=True) for row in items],
            "total": len(rows),
            "page": page,
            "page_size": page_size,
        },
    )


@router.get("/consultations/{case_id}")
def consultation_detail(case_id: int, request: Request, user: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict:
    _current_admin(user, db)
    row = db.scalar(select(Consultation).where(Consultation.id == case_id, Consultation.is_deleted == 0))
    if not row:
        raise HTTPException(status_code=404, detail="问诊单不存在")
    return response_envelope(request, build_consultation_detail(db, row, include_patient=True))


@router.post("/consultations/{case_id}/close")
def close_consultation(case_id: int, request: Request, user: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict:
    _current_admin(user, db)
    row = db.scalar(select(Consultation).where(Consultation.id == case_id, Consultation.is_deleted == 0))
    if not row:
        raise HTTPException(status_code=404, detail="问诊单不存在")
    row.status = "CLOSED"
    row.closed_at = datetime.utcnow()
    row.updated_at = datetime.utcnow()
    log_operation(db, user.id, user.role_type, "ADMIN", "CLOSE_CASE", str(row.id), f"管理员关闭问诊单 {row.case_no}", request.client.host if request.client else None)
    db.commit()
    return response_envelope(request, {"case_id": row.id, "status": row.status}, "处理完成")


@router.get("/configs")
def configs(request: Request, user: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict:
    _current_admin(user, db)
    rows = db.execute(select(SystemConfig).order_by(SystemConfig.config_group.asc(), SystemConfig.config_key.asc())).scalars().all()
    return response_envelope(
        request,
        [
            {
                "config_id": row.id,
                "config_key": row.config_key,
                "config_value": row.config_value,
                "config_group": row.config_group,
                "description": row.description,
                "updated_at": row.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for row in rows
        ],
    )


@router.put("/configs/{config_key}")
def update_config(
    config_key: str,
    payload: ConfigUpdateIn,
    request: Request,
    user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db),
) -> dict:
    _current_admin(user, db)
    row = db.scalar(select(SystemConfig).where(SystemConfig.config_key == config_key))
    if not row:
        raise HTTPException(status_code=404, detail="配置项不存在")
    row.config_value = payload.config_value
    row.updated_by = user.id
    row.updated_at = datetime.utcnow()
    log_operation(db, user.id, user.role_type, "CONFIG", "UPDATE", row.config_key, f"更新系统配置 {row.config_key}", request.client.host if request.client else None)
    db.commit()
    return response_envelope(request, {"config_key": row.config_key, "config_value": row.config_value}, "配置已保存")


@router.post("/announcements")
def create_announcement(
    payload: AnnouncementIn,
    request: Request,
    user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db),
) -> dict:
    _current_admin(user, db)
    row = Announcement(
        title=payload.title,
        content=payload.content,
        status=payload.status,
        publish_scope=payload.publish_scope,
        published_by=user.id,
        published_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(row)
    log_operation(db, user.id, user.role_type, "ANNOUNCEMENT", "CREATE", str(row.id or ""), f"创建公告 {payload.title}", request.client.host if request.client else None)
    db.commit()
    return response_envelope(request, {"announcement_id": row.id}, "公告已发布")


@router.put("/announcements/{announcement_id}")
def update_announcement(
    announcement_id: int,
    payload: AnnouncementIn,
    request: Request,
    user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db),
) -> dict:
    _current_admin(user, db)
    row = db.scalar(select(Announcement).where(Announcement.id == announcement_id))
    if not row:
        raise HTTPException(status_code=404, detail="公告不存在")
    row.title = payload.title
    row.content = payload.content
    row.publish_scope = payload.publish_scope
    row.status = payload.status
    row.published_at = datetime.utcnow()
    row.updated_at = datetime.utcnow()
    log_operation(db, user.id, user.role_type, "ANNOUNCEMENT", "UPDATE", str(row.id), f"更新公告 {payload.title}", request.client.host if request.client else None)
    db.commit()
    return response_envelope(request, {"announcement_id": row.id}, "公告已更新")


@router.delete("/announcements/{announcement_id}")
def delete_announcement(announcement_id: int, request: Request, user: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict:
    _current_admin(user, db)
    row = db.scalar(select(Announcement).where(Announcement.id == announcement_id))
    if not row:
        raise HTTPException(status_code=404, detail="公告不存在")
    db.delete(row)
    log_operation(db, user.id, user.role_type, "ANNOUNCEMENT", "DELETE", str(announcement_id), f"删除公告 {announcement_id}", request.client.host if request.client else None)
    db.commit()
    return response_envelope(request, {"announcement_id": announcement_id}, "已删除")


@router.get("/stats/overview")
def stats_overview(request: Request, user: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict:
    _current_admin(user, db)
    ensure_chat_tables(db)
    users_total = len(db.execute(select(User).where(User.role_type == "USER", User.is_deleted == 0)).scalars().all())
    doctors_total = len(db.execute(select(Doctor)).scalars().all())
    cases = db.execute(select(Consultation).where(Consultation.is_deleted == 0)).scalars().all()
    chat_sessions_total = len(db.execute(select(ChatSession)).scalars().all())
    chat_messages_total = len(db.execute(select(ChatMessage).where(ChatMessage.role == "assistant")).scalars().all())
    web_search_total = len(db.execute(select(ToolCallLog).where(ToolCallLog.tool_name == "tavily")).scalars().all())
    return response_envelope(
        request,
        {
            "users_total": users_total,
            "doctors_total": doctors_total,
            "consultations_total": len(cases),
            "high_risk_total": len([row for row in cases if row.risk_level == "HIGH"]),
            "pending_doctor_total": len([row for row in cases if row.status == "WAIT_DOCTOR"]),
            "chat_sessions_total": chat_sessions_total,
            "chat_messages_total": chat_messages_total,
            "web_search_total": web_search_total,
        },
    )


@router.get("/stats/consultation-trend")
def consultation_trend(request: Request, user: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict:
    _current_admin(user, db)
    rows = db.execute(select(StatisticsSnapshot).where(StatisticsSnapshot.metric_group == "consultation").order_by(StatisticsSnapshot.snapshot_date.asc())).scalars().all()
    return response_envelope(
        request,
        [
            {
                "snapshot_date": row.snapshot_date.isoformat(),
                "metric_key": row.metric_key,
                "metric_value": row.metric_value,
            }
            for row in rows
        ],
    )


@router.get("/stats/hot-questions")
def hot_questions(request: Request, user: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict:
    _current_admin(user, db)
    ensure_chat_tables(db)
    rows = (
        db.execute(
            select(ChatMessage)
            .where(ChatMessage.role == "user")
            .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
        )
        .scalars()
        .all()
    )
    counter: Counter[str] = Counter()
    latest_time: dict[str, str] = {}
    for row in rows:
        key = row.content[:18]
        counter[key] += 1
        latest_time[key] = row.created_at.strftime("%Y-%m-%d %H:%M:%S")
    return response_envelope(
        request,
        [
            {"question": key, "count": count, "latest_time": latest_time[key]}
            for key, count in counter.most_common(10)
        ],
    )


@router.get("/logs/operations")
def operation_logs(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db),
) -> dict:
    _current_admin(user, db)
    rows = db.execute(select(OperationLog).order_by(OperationLog.created_at.desc())).scalars().all()
    start = (page - 1) * page_size
    items = rows[start : start + page_size]
    return response_envelope(
        request,
        {
            "list": [
                {
                    "log_id": row.id,
                    "account_id": row.account_id,
                    "role_type": row.role_type,
                    "module_name": row.module_name,
                    "operation_type": row.operation_type,
                    "business_id": row.business_id,
                    "operation_desc": row.operation_desc,
                    "request_ip": row.request_ip,
                    "operation_result": row.operation_result,
                    "created_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for row in items
            ],
            "total": len(rows),
            "page": page,
            "page_size": page_size,
        },
    )


@router.get("/logs/errors")
def error_logs(request: Request, user: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict:
    _current_admin(user, db)
    rows = db.execute(select(OperationLog).where(OperationLog.operation_result != "SUCCESS").order_by(OperationLog.created_at.desc())).scalars().all()
    return response_envelope(
        request,
        [
            {
                "log_id": row.id,
                "module_name": row.module_name,
                "operation_type": row.operation_type,
                "operation_desc": row.operation_desc,
                "created_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for row in rows
        ],
    )


@router.get("/logs/model-calls")
def model_call_logs(request: Request, user: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict:
    _current_admin(user, db)
    ensure_chat_tables(db)
    ai_rows = db.execute(select(AIAnalysisRecord).order_by(AIAnalysisRecord.created_at.desc())).scalars().all()
    chat_rows = (
        db.execute(
            select(ChatMessage)
            .where(ChatMessage.role == "assistant")
            .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
        )
        .scalars()
        .all()
    )
    tool_logs = {
        row.message_id: row
        for row in db.execute(select(ToolCallLog).order_by(ToolCallLog.created_at.desc(), ToolCallLog.id.desc())).scalars().all()
        if row.message_id
    }
    data = [
        {
            "biz_type": "AI_ANALYSIS",
            "record_id": row.id,
            "model_name": row.model_name,
            "status": row.analysis_status,
            "summary": row.image_observation[:60] if row.image_observation else "",
            "created_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for row in ai_rows[:40]
    ] + [
        {
            "biz_type": "TEXT_QA_WEB" if tool_logs.get(row.id) else "TEXT_QA_DIRECT",
            "record_id": row.id,
            "model_name": row.model_name,
            "status": "FAILED" if tool_logs.get(row.id) and not tool_logs[row.id].success else "SUCCESS",
            "summary": row.content[:60],
            "created_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for row in chat_rows[:40]
    ]
    data.sort(key=lambda item: item["created_at"], reverse=True)
    return response_envelope(request, data[:80])
