from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.middleware import response_envelope
from app.model import Consultation, ConsultationMessage, ConsultationReply, Doctor, DoctorAIFeedback, User
from app.routes.deps import require_roles
from app.schema import DoctorAIFeedbackIn, DoctorReplyIn
from app.service import (
    build_consultation_detail,
    build_patient_tags,
    build_reply_content,
    calculate_health_score,
    compute_accuracy_score,
    create_notification,
    ensure_user_profile,
    group_daily_counts,
    latest_ai,
    latest_ai_feedback,
    latest_reply,
    log_operation,
    split_text_segments,
)


router = APIRouter()
RISK_PRIORITY = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, None: 3}
STATUS_PRIORITY = {"WAIT_DOCTOR": 0, "DOCTOR_REPLIED": 1, "AI_DONE": 2, "CLOSED": 3}


def _current_doctor(user: User, db: Session) -> Doctor:
    doctor = db.scalar(select(Doctor).where(Doctor.user_id == user.id))
    if not doctor:
        raise HTTPException(status_code=404, detail="医生资料不存在")
    return doctor


def _doctor_case(doctor: Doctor, case_id: int, db: Session) -> Consultation:
    case = db.scalar(
        select(Consultation).where(
            Consultation.id == case_id,
            Consultation.assigned_doctor_id == doctor.id,
            Consultation.is_deleted == 0,
        )
    )
    if not case:
        raise HTTPException(status_code=404, detail="问诊单不存在或未分配给当前医生")
    return case


def _doctor_cases(doctor: Doctor, db: Session) -> list[Consultation]:
    return db.execute(
        select(Consultation)
        .where(Consultation.assigned_doctor_id == doctor.id, Consultation.is_deleted == 0)
        .order_by(Consultation.created_at.desc(), Consultation.id.desc())
    ).scalars().all()


@router.get("/dashboard")
def dashboard(request: Request, user: User = Depends(require_roles("DOCTOR")), db: Session = Depends(get_db)) -> dict:
    doctor = _current_doctor(user, db)
    rows = _doctor_cases(doctor, db)
    replies = db.execute(
        select(ConsultationReply)
        .where(ConsultationReply.doctor_id == doctor.id)
        .order_by(ConsultationReply.created_at.desc(), ConsultationReply.id.desc())
    ).scalars().all()
    feedback_rows = db.execute(
        select(DoctorAIFeedback)
        .where(DoctorAIFeedback.doctor_id == doctor.id)
        .order_by(DoctorAIFeedback.created_at.desc(), DoctorAIFeedback.id.desc())
    ).scalars().all()

    today = datetime.utcnow().date()
    pending_cases = [row for row in rows if row.status == "WAIT_DOCTOR"]
    high_risk_cases = [row for row in pending_cases if row.risk_level == "HIGH"]
    processed_today = len([row for row in replies if row.created_at.date() == today])
    accuracy = compute_accuracy_score([row.ai_accuracy or "" for row in feedback_rows if row.ai_accuracy])

    queue = sorted(
        rows,
        key=lambda item: (
            STATUS_PRIORITY.get(item.status, 99),
            RISK_PRIORITY.get(item.risk_level, 99),
            item.submitted_at or item.created_at,
        ),
    )
    focus_case = high_risk_cases[0] if high_risk_cases else (pending_cases[0] if pending_cases else (rows[0] if rows else None))

    reply_trend = group_daily_counts([row.created_at for row in replies], total_days=7)
    high_risk_trend = group_daily_counts(
        [row.submitted_at or row.created_at for row in rows if row.risk_level == "HIGH"],
        total_days=7,
    )
    trend = [
        {
            "label": reply_trend[index]["date"].strftime("%m-%d"),
            "consultations": reply_trend[index]["count"],
            "highRisk": high_risk_trend[index]["count"],
        }
        for index in range(len(reply_trend))
    ]

    alert_items = []
    for row in high_risk_cases[:4]:
        detail = build_consultation_detail(db, row, include_patient=True)
        alert_items.append(
            {
                "case_id": row.id,
                "case_no": row.case_no,
                "summary_title": row.summary_title,
                "submitted_at": row.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if row.submitted_at else None,
                "risk_level": row.risk_level,
                "patient": detail.get("patient"),
                "alert": detail.get("ai_result", {}).get("high_risk_alert") if detail.get("ai_result") else "",
            }
        )

    return response_envelope(
        request,
        {
            "doctor": {
                "doctor_id": doctor.id,
                "doctor_name": doctor.doctor_name,
                "department": doctor.department,
                "title_name": doctor.title_name,
                "hospital_name": doctor.hospital_name,
                "audit_status": doctor.audit_status,
                "service_status": doctor.service_status,
                "specialty": doctor.specialty,
            },
            "stats": {
                "pending_total": len(pending_cases),
                "processed_today": processed_today,
                "high_risk_total": len(high_risk_cases),
                "ai_feedback_accuracy": accuracy,
                "replied_total": len(replies),
            },
            "priority_queue": [build_consultation_detail(db, row, include_patient=True) for row in queue[:6]],
            "focus_case": build_consultation_detail(db, focus_case, include_patient=True) if focus_case else None,
            "trend": trend,
            "high_risk_alerts": alert_items,
        },
    )


@router.get("/consultations")
def consultation_list(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    status: str | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    user: User = Depends(require_roles("DOCTOR")),
    db: Session = Depends(get_db),
) -> dict:
    doctor = _current_doctor(user, db)
    rows = _doctor_cases(doctor, db)
    keyword_text = keyword.lower().strip() if keyword else ""

    filtered: list[Consultation] = []
    for row in rows:
        if status and row.status != status:
            continue
        if risk_level and row.risk_level != risk_level:
            continue
        if keyword_text:
            detail = build_consultation_detail(db, row, include_patient=True)
            patient = detail.get("patient", {})
            haystack = " ".join(
                [
                    row.case_no or "",
                    row.summary_title or "",
                    row.chief_complaint or "",
                    patient.get("profile", {}).get("real_name", "") if patient else "",
                    patient.get("account", {}).get("phone", "") if patient else "",
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
def consultation_detail(case_id: int, request: Request, user: User = Depends(require_roles("DOCTOR")), db: Session = Depends(get_db)) -> dict:
    doctor = _current_doctor(user, db)
    case = _doctor_case(doctor, case_id, db)
    return response_envelope(request, build_consultation_detail(db, case, include_patient=True))


@router.post("/consultations/{case_id}/reply")
def reply_consultation(
    case_id: int,
    payload: DoctorReplyIn,
    request: Request,
    user: User = Depends(require_roles("DOCTOR")),
    db: Session = Depends(get_db),
) -> dict:
    doctor = _current_doctor(user, db)
    case = _doctor_case(doctor, case_id, db)

    first_impression = (payload.first_impression or "").strip()
    care_advice = (payload.care_advice or "").strip()
    content = build_reply_content(first_impression, care_advice, payload.doctor_remark, payload.content)
    if not content:
        raise HTTPException(status_code=400, detail="请至少填写医生意见或护理建议")

    reply = latest_reply(db, case.id)
    now = datetime.utcnow()
    if reply and reply.doctor_id == doctor.id:
        reply.content = content
        reply.first_impression = first_impression or reply.first_impression
        reply.care_advice = care_advice or reply.care_advice
        reply.suggest_offline_visit = payload.suggest_offline_visit
        reply.suggest_follow_up = payload.suggest_follow_up
        reply.doctor_remark = payload.doctor_remark
        reply.updated_at = now
    else:
        reply = ConsultationReply(
            consultation_id=case.id,
            doctor_id=doctor.id,
            content=content,
            first_impression=first_impression or None,
            care_advice=care_advice or None,
            suggest_offline_visit=payload.suggest_offline_visit,
            suggest_follow_up=payload.suggest_follow_up,
            doctor_remark=payload.doctor_remark,
            created_at=now,
            updated_at=now,
        )
        db.add(reply)

    db.add(
        ConsultationMessage(
            consultation_id=case.id,
            sender_role="DOCTOR",
            sender_id=user.id,
            message_type="TEXT",
            content=content,
            created_at=now,
        )
    )
    case.status = "DOCTOR_REPLIED"
    case.updated_at = now
    create_notification(
        db,
        case.user_id,
        "医生已回复问诊",
        f"问诊单 {case.case_no} 已收到医生建议，请及时查看。",
        "CONSULTATION",
        "CONSULTATION",
        case.id,
    )
    log_operation(
        db,
        user.id,
        user.role_type,
        "DOCTOR",
        "REPLY",
        str(case.id),
        f"回复问诊单 {case.case_no}",
        request.client.host if request.client else None,
    )
    db.commit()
    return response_envelope(request, {"reply_id": reply.id, "status": case.status}, "回复成功")


@router.post("/consultations/{case_id}/ai-feedback")
def ai_feedback(
    case_id: int,
    payload: DoctorAIFeedbackIn,
    request: Request,
    user: User = Depends(require_roles("DOCTOR")),
    db: Session = Depends(get_db),
) -> dict:
    doctor = _current_doctor(user, db)
    case = _doctor_case(doctor, case_id, db)
    feedback = DoctorAIFeedback(
        consultation_id=case.id,
        doctor_id=doctor.id,
        ai_accuracy=payload.ai_accuracy,
        correction_note=payload.correction_note,
        knowledge_gap_note=payload.knowledge_gap_note,
        created_at=datetime.utcnow(),
    )
    db.add(feedback)
    log_operation(
        db,
        user.id,
        user.role_type,
        "DOCTOR",
        "AI_FEEDBACK",
        str(case.id),
        f"提交 AI 反馈 {payload.ai_accuracy}",
        request.client.host if request.client else None,
    )
    db.commit()
    return response_envelope(request, {"feedback_id": feedback.id}, "反馈已保存")


@router.get("/patients")
def patient_list(
    request: Request,
    keyword: str | None = Query(default=None),
    user: User = Depends(require_roles("DOCTOR")),
    db: Session = Depends(get_db),
) -> dict:
    doctor = _current_doctor(user, db)
    rows = _doctor_cases(doctor, db)
    patient_ids = list(dict.fromkeys([row.user_id for row in rows]))
    keyword_text = keyword.lower().strip() if keyword else ""
    data = []

    for patient_id in patient_ids:
        patient = db.scalar(select(User).where(User.id == patient_id, User.is_deleted == 0))
        if not patient:
            continue
        profile, health = ensure_user_profile(db, patient.id)
        patient_cases = [row for row in rows if row.user_id == patient.id]
        latest_case = patient_cases[0] if patient_cases else None
        name = profile.real_name or patient.username
        haystack = " ".join(
            [
                name,
                patient.phone or "",
                patient.email or "",
                latest_case.summary_title if latest_case and latest_case.summary_title else "",
            ]
        ).lower()
        if keyword_text and keyword_text not in haystack:
            continue

        data.append(
            {
                "account": {
                    "account_id": patient.id,
                    "username": patient.username,
                    "phone": patient.phone,
                    "email": patient.email,
                },
                "profile": {
                    "user_id": patient.id,
                    "real_name": name,
                    "gender": profile.gender,
                    "age": profile.age,
                    "city": profile.city,
                    "occupation": profile.occupation,
                },
                "health_profile": {
                    "skin_type": health.skin_type if health else "",
                    "skin_sensitivity": health.skin_sensitivity if health else "",
                    "allergy_history": health.allergy_history if health else "",
                    "past_medical_history": health.past_medical_history if health else "",
                    "medication_history": health.medication_history if health else "",
                    "sleep_pattern": health.sleep_pattern if health else "",
                    "diet_preference": health.diet_preference if health else "",
                    "special_notes": health.special_notes if health else "",
                },
                "tags": build_patient_tags(health, latest_case),
                "health_score": calculate_health_score(health, patient_cases),
                "latest_case": build_consultation_detail(db, latest_case, include_patient=False) if latest_case else None,
                "recent_case_count": len(patient_cases),
            }
        )

    return response_envelope(request, data)


@router.get("/patients/{user_id}")
def patient_detail(user_id: int, request: Request, user: User = Depends(require_roles("DOCTOR")), db: Session = Depends(get_db)) -> dict:
    doctor = _current_doctor(user, db)
    rows = db.execute(
        select(Consultation)
        .where(
            Consultation.assigned_doctor_id == doctor.id,
            Consultation.user_id == user_id,
            Consultation.is_deleted == 0,
        )
        .order_by(Consultation.created_at.desc(), Consultation.id.desc())
    ).scalars().all()
    if not rows:
        raise HTTPException(status_code=404, detail="当前医生暂无该患者档案")

    patient = db.scalar(select(User).where(User.id == user_id, User.is_deleted == 0))
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    profile, health = ensure_user_profile(db, patient.id)

    history_items = [build_consultation_detail(db, row, include_patient=False) for row in rows[:12]]
    trend_points = []
    for row in list(reversed(rows[:6])):
        trend_points.append(
            {
                "label": (row.submitted_at or row.created_at).strftime("%m-%d"),
                "consultations": {"LOW": 35, "MEDIUM": 62, "HIGH": 88}.get(row.risk_level, 50),
                "highRisk": 1 if row.risk_level == "HIGH" else 0,
            }
        )

    care_suggestions: list[str] = []
    for row in rows:
        ai_record = latest_ai(db, row.id)
        reply = latest_reply(db, row.id)
        for segment in split_text_segments(ai_record.care_advice if ai_record else None):
            if segment not in care_suggestions:
                care_suggestions.append(segment)
        for segment in split_text_segments(reply.care_advice if reply else None):
            if segment not in care_suggestions:
                care_suggestions.append(segment)
        if len(care_suggestions) >= 5:
            break

    follow_up_cases = []
    for row in rows:
        reply = latest_reply(db, row.id)
        if reply and reply.suggest_follow_up:
            follow_up_cases.append(
                {
                    "case_id": row.id,
                    "case_no": row.case_no,
                    "summary_title": row.summary_title,
                    "reply_time": reply.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

    return response_envelope(
        request,
        {
            "account": {
                "account_id": patient.id,
                "username": patient.username,
                "phone": patient.phone,
                "email": patient.email,
            },
            "profile": {
                "user_id": patient.id,
                "real_name": profile.real_name or patient.username,
                "gender": profile.gender,
                "age": profile.age,
                "city": profile.city,
                "occupation": profile.occupation,
                "remark": profile.remark,
            },
            "health_profile": {
                "allergy_history": health.allergy_history if health else "",
                "past_medical_history": health.past_medical_history if health else "",
                "medication_history": health.medication_history if health else "",
                "skin_type": health.skin_type if health else "",
                "skin_sensitivity": health.skin_sensitivity if health else "",
                "sleep_pattern": health.sleep_pattern if health else "",
                "diet_preference": health.diet_preference if health else "",
                "special_notes": health.special_notes if health else "",
            },
            "tags": build_patient_tags(health, rows[0] if rows else None),
            "health_score": calculate_health_score(health, rows),
            "history_cases": history_items,
            "risk_trend": trend_points,
            "care_suggestions": care_suggestions[:5],
            "follow_up_cases": follow_up_cases[:5],
        },
    )


@router.get("/history")
def reply_history(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    user: User = Depends(require_roles("DOCTOR")),
    db: Session = Depends(get_db),
) -> dict:
    doctor = _current_doctor(user, db)
    rows = db.execute(
        select(ConsultationReply)
        .where(ConsultationReply.doctor_id == doctor.id)
        .order_by(ConsultationReply.created_at.desc(), ConsultationReply.id.desc())
    ).scalars().all()
    consultations = {row.id: row for row in db.execute(select(Consultation)).scalars().all()}
    start = (page - 1) * page_size
    items = rows[start : start + page_size]
    return response_envelope(
        request,
        {
            "list": [
                {
                    "reply_id": row.id,
                    "consultation_id": row.consultation_id,
                    "case_no": consultations[row.consultation_id].case_no if row.consultation_id in consultations else "",
                    "summary_title": consultations[row.consultation_id].summary_title if row.consultation_id in consultations else "",
                    "content": row.content,
                    "first_impression": row.first_impression,
                    "care_advice": row.care_advice,
                    "created_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for row in items
            ],
            "total": len(rows),
            "page": page,
            "page_size": page_size,
        },
    )
