from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.middleware import response_envelope
from app.model import AIAnalysisRecord, Admin, Announcement, Consultation, ConsultationReply, Doctor, OperationLog, SystemConfig, User, UserProfile
from app.routes.deps import require_roles
from app.schema import AnnouncementIn, AuditUpdateIn, ConfigUpdateIn, ConsultationArchiveIn, ConsultationFlagIn, StatusUpdateIn
from app.service import (
    build_consultation_detail,
    build_patient_tags,
    calculate_health_score,
    ensure_user_profile,
    get_config_map,
    get_json_config,
    group_daily_counts,
    latest_ai,
    latest_reply,
    log_operation,
    serialize_account,
    serialize_health,
    serialize_profile,
    upsert_default_system_configs,
)


router = APIRouter()


def _current_admin(user: User, db: Session) -> Admin:
    admin = db.scalar(select(Admin).where(Admin.user_id == user.id))
    if not admin:
        raise HTTPException(status_code=404, detail="管理员资料不存在")
    return admin


def _serialize_config(row: SystemConfig) -> dict:
    value_type = "text"
    try:
        parsed = json.loads(row.config_value)
        if isinstance(parsed, bool):
            value_type = "boolean"
        elif isinstance(parsed, (int, float)):
            value_type = "number"
        elif isinstance(parsed, (dict, list)):
            value_type = "json"
    except json.JSONDecodeError:
        lower = row.config_value.strip().lower()
        if lower in {"true", "false"}:
            value_type = "boolean"
        else:
            try:
                float(row.config_value)
                value_type = "number"
            except ValueError:
                value_type = "textarea" if len(row.config_value) > 120 else "text"

    return {
        "config_id": row.id,
        "config_key": row.config_key,
        "config_value": row.config_value,
        "config_group": row.config_group,
        "description": row.description,
        "value_type": value_type,
        "updated_at": row.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


@router.get("/dashboard")
def dashboard(request: Request, user: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict:
    _current_admin(user, db)
    rows = db.execute(select(Consultation).where(Consultation.is_deleted == 0).order_by(Consultation.created_at.desc(), Consultation.id.desc())).scalars().all()
    doctors = db.execute(select(Doctor).order_by(Doctor.created_at.desc(), Doctor.id.desc())).scalars().all()
    users = db.execute(select(User).where(User.role_type == "USER", User.is_deleted == 0)).scalars().all()
    replies = db.execute(select(ConsultationReply).order_by(ConsultationReply.created_at.desc(), ConsultationReply.id.desc())).scalars().all()
    ai_logs = db.execute(select(AIAnalysisRecord).order_by(AIAnalysisRecord.created_at.desc(), AIAnalysisRecord.id.desc())).scalars().all()
    operation_logs = db.execute(select(OperationLog).order_by(OperationLog.created_at.desc(), OperationLog.id.desc())).scalars().all()

    today = datetime.utcnow().date()
    active_doctor_ids = {row.doctor_id for row in replies if row.created_at.date() == today}
    trend_consultation = group_daily_counts([row.submitted_at or row.created_at for row in rows], total_days=7)
    trend_high_risk = group_daily_counts([row.submitted_at or row.created_at for row in rows if row.risk_level == "HIGH"], total_days=7)
    trend = [
        {
            "label": trend_consultation[index]["date"].strftime("%m-%d"),
            "consultations": trend_consultation[index]["count"],
            "highRisk": trend_high_risk[index]["count"],
        }
        for index in range(len(trend_consultation))
    ]

    doctor_overview = []
    for doctor in doctors[:8]:
        doctor_replies = [row for row in replies if row.doctor_id == doctor.id]
        doctor_cases = [row for row in rows if row.assigned_doctor_id == doctor.id]
        response_rate = 0 if not doctor_cases else round(len(doctor_replies) / len(doctor_cases) * 100, 1)
        doctor_user = db.scalar(select(User).where(User.id == doctor.user_id))
        doctor_overview.append(
            {
                "doctor_id": doctor.id,
                "doctor_name": doctor.doctor_name,
                "department": doctor.department,
                "title_name": doctor.title_name,
                "service_status": doctor.service_status,
                "audit_status": doctor.audit_status,
                "response_rate": response_rate,
                "today_processed": len([row for row in doctor_replies if row.created_at.date() == today]),
                "account": serialize_account(doctor_user),
            }
        )

    pending_doctors = []
    for doctor in [row for row in doctors if row.audit_status == "PENDING"][:5]:
        doctor_user = db.scalar(select(User).where(User.id == doctor.user_id))
        pending_doctors.append(
            {
                "doctor_id": doctor.id,
                "doctor_name": doctor.doctor_name,
                "department": doctor.department,
                "title_name": doctor.title_name,
                "hospital_name": doctor.hospital_name,
                "submitted_at": doctor.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "phone": doctor_user.phone if doctor_user else "",
            }
        )

    alerts = []
    for row in [item for item in rows if item.status == "WAIT_DOCTOR" and item.risk_level == "HIGH"][:4]:
        detail = build_consultation_detail(db, row, include_patient=True)
        alerts.append(
            {
                "type": "HIGH_RISK_CASE",
                "case_id": row.id,
                "case_no": row.case_no,
                "summary_title": row.summary_title,
                "patient_name": detail.get("patient", {}).get("profile", {}).get("real_name", ""),
                "time": row.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if row.submitted_at else None,
            }
        )
    for record in [item for item in ai_logs if item.analysis_status != "SUCCESS"][:3]:
        alerts.append(
            {
                "type": "AI_FALLBACK",
                "record_id": record.id,
                "case_id": record.consultation_id,
                "summary_title": record.fail_reason or "AI 调用异常，已回退到兜底策略",
                "time": record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    latest_activities = [
        {
            "log_id": row.id,
            "module_name": row.module_name,
            "operation_type": row.operation_type,
            "operation_desc": row.operation_desc,
            "created_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "operation_result": row.operation_result,
        }
        for row in operation_logs[:8]
    ]

    error_logs = [row for row in operation_logs if row.operation_result and row.operation_result != "SUCCESS"]
    avg_response_seconds = 0.0
    response_samples = []
    for row in rows:
        reply = latest_reply(db, row.id)
        if row.submitted_at and reply:
            response_samples.append((reply.created_at - row.submitted_at).total_seconds())
    if response_samples:
        avg_response_seconds = round(sum(response_samples) / len(response_samples), 2)

    return response_envelope(
        request,
        {
            "metrics": {
                "users_total": len(users),
                "doctors_total": len(doctors),
                "consultations_total": len(rows),
                "high_risk_total": len([row for row in rows if row.risk_level == "HIGH"]),
                "ai_calls_total": len(ai_logs),
                "active_doctors_today": len(active_doctor_ids),
            },
            "trend": trend,
            "runtime": {
                "model_status": "NORMAL" if not [row for row in ai_logs[:20] if row.analysis_status == "FAILED"] else "DEGRADED",
                "queue_waiting": len([row for row in rows if row.status == "WAIT_DOCTOR"]),
                "avg_response_seconds": avg_response_seconds,
                "error_rate": round((len(error_logs) / max(len(operation_logs), 1)) * 100, 2),
            },
            "doctor_overview": doctor_overview,
            "pending_doctors": pending_doctors,
            "latest_activities": latest_activities,
            "alerts": alerts[:6],
        },
    )


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
    rows = db.execute(select(User).where(User.role_type == "USER", User.is_deleted == 0).order_by(User.created_at.desc(), User.id.desc())).scalars().all()
    keyword_text = keyword.lower().strip() if keyword else ""
    profiles = {profile.user_id: profile for profile in db.execute(select(UserProfile)).scalars().all()}
    filtered = []
    for row in rows:
        profile = profiles.get(row.id)
        if status is not None and row.status != status:
            continue
        haystack = " ".join([row.username, row.phone or "", row.email or "", profile.real_name if profile and profile.real_name else ""]).lower()
        if keyword_text and keyword_text not in haystack:
            continue
        consultations = db.execute(
            select(Consultation)
            .where(Consultation.user_id == row.id, Consultation.is_deleted == 0)
            .order_by(Consultation.created_at.desc(), Consultation.id.desc())
        ).scalars().all()
        filtered.append(
            {
                "account": serialize_account(row),
                "profile": serialize_profile(row, profile),
                "stats": {
                    "consultation_total": len(consultations),
                    "latest_case_title": consultations[0].summary_title if consultations else "",
                    "latest_case_time": consultations[0].submitted_at.strftime("%Y-%m-%d %H:%M:%S") if consultations and consultations[0].submitted_at else None,
                },
            }
        )

    start = (page - 1) * page_size
    items = filtered[start : start + page_size]
    return response_envelope(request, {"list": items, "total": len(filtered), "page": page, "page_size": page_size})


@router.get("/users/{user_id}")
def user_detail(user_id: int, request: Request, user: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict:
    _current_admin(user, db)
    target = db.scalar(select(User).where(User.id == user_id, User.role_type == "USER", User.is_deleted == 0))
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")
    profile, health = ensure_user_profile(db, target.id)
    consultations = db.execute(
        select(Consultation)
        .where(Consultation.user_id == target.id, Consultation.is_deleted == 0)
        .order_by(Consultation.created_at.desc(), Consultation.id.desc())
    ).scalars().all()
    return response_envelope(
        request,
        {
            "account": serialize_account(target),
            "profile": serialize_profile(target, profile),
            "health_profile": serialize_health(health),
            "tags": build_patient_tags(health, consultations[0] if consultations else None),
            "health_score": calculate_health_score(health, consultations),
            "recent_consultations": [build_consultation_detail(db, row, include_patient=False) for row in consultations[:10]],
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
    service_status: int | None = Query(default=None),
    user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db),
) -> dict:
    _current_admin(user, db)
    rows = db.execute(select(Doctor).order_by(Doctor.created_at.desc(), Doctor.id.desc())).scalars().all()
    keyword_text = keyword.lower().strip() if keyword else ""
    filtered = []
    for row in rows:
        account = db.scalar(select(User).where(User.id == row.user_id))
        if audit_status and row.audit_status != audit_status:
            continue
        if service_status is not None and row.service_status != service_status:
            continue
        haystack = " ".join([row.doctor_name, row.department or "", row.hospital_name or "", account.phone if account and account.phone else ""]).lower()
        if keyword_text and keyword_text not in haystack:
            continue
        doctor_cases = db.execute(select(Consultation).where(Consultation.assigned_doctor_id == row.id, Consultation.is_deleted == 0)).scalars().all()
        doctor_replies = db.execute(select(ConsultationReply).where(ConsultationReply.doctor_id == row.id)).scalars().all()
        response_rate = 0 if not doctor_cases else round(len(doctor_replies) / len(doctor_cases) * 100, 1)
        filtered.append(
            {
                "doctor_id": row.id,
                "account": serialize_account(account),
                "doctor_name": row.doctor_name,
                "department": row.department,
                "title_name": row.title_name,
                "hospital_name": row.hospital_name,
                "specialty": row.specialty,
                "intro": row.intro,
                "license_no": row.license_no,
                "audit_status": row.audit_status,
                "audit_remark": row.audit_remark,
                "service_status": row.service_status,
                "created_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "stats": {
                    "consultation_total": len(doctor_cases),
                    "response_rate": response_rate,
                    "online_status": "服务中" if row.service_status == 1 else "已暂停",
                },
            }
        )
    start = (page - 1) * page_size
    items = filtered[start : start + page_size]
    return response_envelope(request, {"list": items, "total": len(filtered), "page": page, "page_size": page_size})


@router.get("/doctors/{doctor_id}")
def doctor_detail(doctor_id: int, request: Request, user: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict:
    _current_admin(user, db)
    doctor = db.scalar(select(Doctor).where(Doctor.id == doctor_id))
    if not doctor:
        raise HTTPException(status_code=404, detail="医生不存在")
    account = db.scalar(select(User).where(User.id == doctor.user_id))
    doctor_cases = db.execute(
        select(Consultation)
        .where(Consultation.assigned_doctor_id == doctor.id, Consultation.is_deleted == 0)
        .order_by(Consultation.created_at.desc(), Consultation.id.desc())
    ).scalars().all()
    doctor_replies = db.execute(select(ConsultationReply).where(ConsultationReply.doctor_id == doctor.id)).scalars().all()
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
            "stats": {
                "consultation_total": len(doctor_cases),
                "reply_total": len(doctor_replies),
                "response_rate": 0 if not doctor_cases else round(len(doctor_replies) / len(doctor_cases) * 100, 1),
                "high_risk_total": len([row for row in doctor_cases if row.risk_level == "HIGH"]),
            },
            "recent_consultations": [build_consultation_detail(db, row, include_patient=True) for row in doctor_cases[:6]],
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
    keyword: str | None = Query(default=None),
    doctor_id: int | None = Query(default=None),
    user_id: int | None = Query(default=None),
    archived_flag: int | None = Query(default=None),
    abnormal_flag: int | None = Query(default=None),
    user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db),
) -> dict:
    _current_admin(user, db)
    rows = db.execute(
        select(Consultation)
        .where(Consultation.is_deleted == 0)
        .order_by(Consultation.created_at.desc(), Consultation.id.desc())
    ).scalars().all()
    keyword_text = keyword.lower().strip() if keyword else ""
    filtered: list[Consultation] = []
    for row in rows:
        if status and row.status != status:
            continue
        if risk_level and row.risk_level != risk_level:
            continue
        if doctor_id is not None and row.assigned_doctor_id != doctor_id:
            continue
        if user_id is not None and row.user_id != user_id:
            continue
        if archived_flag is not None and row.archived_flag != archived_flag:
            continue
        if abnormal_flag is not None and row.abnormal_flag != abnormal_flag:
            continue
        detail = build_consultation_detail(db, row, include_patient=True)
        if keyword_text:
            patient = detail.get("patient", {})
            doctor = detail.get("doctor", {})
            haystack = " ".join(
                [
                    row.case_no or "",
                    row.summary_title or "",
                    row.chief_complaint or "",
                    patient.get("profile", {}).get("real_name", "") if patient else "",
                    patient.get("account", {}).get("phone", "") if patient else "",
                    doctor.get("doctor_name", "") if doctor else "",
                ]
            ).lower()
            if keyword_text not in haystack:
                continue
        filtered.append(row)
    start = (page - 1) * page_size
    items = filtered[start : start + page_size]
    return response_envelope(
        request,
        {
            "list": [build_consultation_detail(db, row, include_patient=True) for row in items],
            "total": len(filtered),
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


@router.put("/consultations/{case_id}/flag")
def flag_consultation(
    case_id: int,
    payload: ConsultationFlagIn,
    request: Request,
    user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db),
) -> dict:
    _current_admin(user, db)
    row = db.scalar(select(Consultation).where(Consultation.id == case_id, Consultation.is_deleted == 0))
    if not row:
        raise HTTPException(status_code=404, detail="问诊单不存在")
    row.abnormal_flag = 1 if payload.abnormal_flag else 0
    row.abnormal_note = payload.abnormal_note
    row.updated_at = datetime.utcnow()
    log_operation(db, user.id, user.role_type, "ADMIN", "FLAG_CASE", str(row.id), f"问诊单异常标记 {row.abnormal_flag}", request.client.host if request.client else None)
    db.commit()
    return response_envelope(request, {"case_id": row.id, "abnormal_flag": row.abnormal_flag}, "已更新异常标记")


@router.put("/consultations/{case_id}/archive")
def archive_consultation(
    case_id: int,
    payload: ConsultationArchiveIn,
    request: Request,
    user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db),
) -> dict:
    _current_admin(user, db)
    row = db.scalar(select(Consultation).where(Consultation.id == case_id, Consultation.is_deleted == 0))
    if not row:
        raise HTTPException(status_code=404, detail="问诊单不存在")
    row.archived_flag = 1 if payload.archived_flag else 0
    row.archived_at = datetime.utcnow() if row.archived_flag else None
    row.updated_at = datetime.utcnow()
    log_operation(db, user.id, user.role_type, "ADMIN", "ARCHIVE_CASE", str(row.id), f"问诊单归档状态 {row.archived_flag}", request.client.host if request.client else None)
    db.commit()
    return response_envelope(request, {"case_id": row.id, "archived_flag": row.archived_flag}, "归档状态已更新")


@router.delete("/consultations/{case_id}")
def delete_consultation(case_id: int, request: Request, user: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict:
    _current_admin(user, db)
    row = db.scalar(select(Consultation).where(Consultation.id == case_id, Consultation.is_deleted == 0))
    if not row:
        raise HTTPException(status_code=404, detail="问诊单不存在")
    row.is_deleted = 1
    row.updated_at = datetime.utcnow()
    log_operation(db, user.id, user.role_type, "ADMIN", "DELETE_CASE", str(row.id), f"软删除问诊单 {row.case_no}", request.client.host if request.client else None)
    db.commit()
    return response_envelope(request, {"case_id": row.id}, "已删除")


@router.get("/configs")
def configs(request: Request, user: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict:
    _current_admin(user, db)
    upsert_default_system_configs(db, user.id)
    db.commit()
    rows = db.execute(select(SystemConfig).order_by(SystemConfig.config_group.asc(), SystemConfig.config_key.asc())).scalars().all()
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row.config_group or "GENERAL", []).append(_serialize_config(row))
    return response_envelope(request, {"groups": grouped, "list": [_serialize_config(row) for row in rows]})


@router.put("/configs/{config_key}")
def update_config(
    config_key: str,
    payload: ConfigUpdateIn,
    request: Request,
    user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db),
) -> dict:
    _current_admin(user, db)
    upsert_default_system_configs(db, user.id)
    row = db.scalar(select(SystemConfig).where(SystemConfig.config_key == config_key))
    if not row:
        raise HTTPException(status_code=404, detail="配置项不存在")

    value = payload.config_value
    if isinstance(value, (dict, list)):
        row.config_value = json.dumps(value, ensure_ascii=False)
    elif isinstance(value, bool):
        row.config_value = "true" if value else "false"
    else:
        row.config_value = str(value)
    row.updated_by = user.id
    row.updated_at = datetime.utcnow()
    log_operation(db, user.id, user.role_type, "CONFIG", "UPDATE", row.config_key, f"更新系统配置 {row.config_key}", request.client.host if request.client else None)
    db.commit()
    return response_envelope(request, _serialize_config(row), "配置已保存")


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
    db.flush()
    log_operation(db, user.id, user.role_type, "ANNOUNCEMENT", "CREATE", str(row.id), f"创建公告 {payload.title}", request.client.host if request.client else None)
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


@router.get("/logs/overview")
def logs_overview(request: Request, user: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict:
    _current_admin(user, db)
    operation_logs = db.execute(select(OperationLog).order_by(OperationLog.created_at.desc(), OperationLog.id.desc())).scalars().all()
    ai_logs = db.execute(select(AIAnalysisRecord).order_by(AIAnalysisRecord.created_at.desc(), AIAnalysisRecord.id.desc())).scalars().all()
    login_logs = [row for row in operation_logs if row.module_name == "AUTH" and row.operation_type == "LOGIN"]
    error_logs = [row for row in operation_logs if row.operation_result and row.operation_result != "SUCCESS"]
    trend_logs = group_daily_counts([row.created_at for row in operation_logs], total_days=7)
    trend_errors = group_daily_counts([row.created_at for row in error_logs], total_days=7)
    trend = [
        {
            "label": trend_logs[index]["date"].strftime("%m-%d"),
            "consultations": trend_logs[index]["count"],
            "highRisk": trend_errors[index]["count"],
        }
        for index in range(len(trend_logs))
    ]

    alerts = []
    for row in error_logs[:5]:
        alerts.append(
            {
                "type": "OPERATION_ERROR",
                "title": f"{row.module_name} / {row.operation_type}",
                "content": row.operation_desc,
                "time": row.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    for row in [item for item in ai_logs if item.analysis_status != "SUCCESS"][:5]:
        alerts.append(
            {
                "type": "AI_FALLBACK",
                "title": row.model_name,
                "content": row.fail_reason or "AI 调用失败，已进入兜底逻辑",
                "time": row.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    return response_envelope(
        request,
        {
            "metrics": {
                "login_total": len(login_logs),
                "operation_total": len(operation_logs),
                "ai_call_total": len(ai_logs),
                "error_total": len(error_logs),
            },
            "trend": trend,
            "recent_logs": [
                {
                    "log_id": row.id,
                    "module_name": row.module_name,
                    "operation_type": row.operation_type,
                    "operation_desc": row.operation_desc,
                    "account_id": row.account_id,
                    "role_type": row.role_type,
                    "request_ip": row.request_ip,
                    "operation_result": row.operation_result,
                    "created_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for row in operation_logs[:20]
            ],
            "alerts": alerts[:10],
            "model_calls": [
                {
                    "record_id": row.id,
                    "consultation_id": row.consultation_id,
                    "model_name": row.model_name,
                    "analysis_status": row.analysis_status,
                    "fail_reason": row.fail_reason,
                    "created_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for row in ai_logs[:20]
            ],
        },
    )


@router.get("/stats/overview")
def stats_overview(request: Request, user: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict:
    _current_admin(user, db)
    config_map = get_config_map(db)
    upload_rules = get_json_config(config_map, "upload.rules", {"max_mb": 10})
    rows = db.execute(select(Consultation).where(Consultation.is_deleted == 0)).scalars().all()
    doctors = db.execute(select(Doctor)).scalars().all()
    users = db.execute(select(User).where(User.role_type == "USER", User.is_deleted == 0)).scalars().all()
    ai_logs = db.execute(select(AIAnalysisRecord)).scalars().all()
    return response_envelope(
        request,
        {
            "users_total": len(users),
            "doctors_total": len(doctors),
            "consultations_total": len(rows),
            "high_risk_total": len([row for row in rows if row.risk_level == "HIGH"]),
            "pending_doctor_total": len([row for row in rows if row.status == "WAIT_DOCTOR"]),
            "ai_call_total": len(ai_logs),
            "upload_max_mb": upload_rules.get("max_mb", 10),
        },
    )
