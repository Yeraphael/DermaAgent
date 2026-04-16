from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.middleware import response_envelope
from app.model import Consultation, ConsultationMessage, ConsultationReply, Doctor, DoctorAIFeedback, User
from app.routes.deps import require_roles
from app.schema import DoctorAIFeedbackIn, DoctorReplyIn
from app.service import build_consultation_detail, create_notification, log_operation


router = APIRouter()


def _current_doctor(user: User, db: Session) -> Doctor:
    doctor = db.scalar(select(Doctor).where(Doctor.user_id == user.id))
    if not doctor:
        raise HTTPException(status_code=404, detail="医生资料不存在")
    return doctor


def _doctor_case(doctor: Doctor, case_id: int, db: Session) -> Consultation:
    case = db.scalar(select(Consultation).where(Consultation.id == case_id, Consultation.assigned_doctor_id == doctor.id, Consultation.is_deleted == 0))
    if not case:
        raise HTTPException(status_code=404, detail="问诊单不存在或未分配给当前医生")
    return case


@router.get("/dashboard")
def dashboard(request: Request, user: User = Depends(require_roles("DOCTOR")), db: Session = Depends(get_db)) -> dict:
    doctor = _current_doctor(user, db)
    rows = db.execute(select(Consultation).where(Consultation.assigned_doctor_id == doctor.id, Consultation.is_deleted == 0).order_by(Consultation.created_at.desc())).scalars().all()
    stats = {
        "pending_total": len([row for row in rows if row.status == "WAIT_DOCTOR"]),
        "replied_total": len([row for row in rows if row.status == "DOCTOR_REPLIED"]),
        "closed_total": len([row for row in rows if row.status == "CLOSED"]),
        "high_risk_total": len([row for row in rows if row.risk_level == "HIGH"]),
    }
    latest_cases = [
        {
            "case_id": row.id,
            "case_no": row.case_no,
            "summary_title": row.summary_title,
            "status": row.status,
            "risk_level": row.risk_level,
            "submitted_at": row.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if row.submitted_at else None,
            "user_id": row.user_id,
        }
        for row in rows[:6]
    ]
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
            },
            "stats": stats,
            "latest_cases": latest_cases,
        },
    )


@router.get("/consultations")
def consultation_list(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    status: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    user: User = Depends(require_roles("DOCTOR")),
    db: Session = Depends(get_db),
) -> dict:
    doctor = _current_doctor(user, db)
    rows = db.execute(select(Consultation).where(Consultation.assigned_doctor_id == doctor.id, Consultation.is_deleted == 0).order_by(Consultation.created_at.desc())).scalars().all()
    if status:
        rows = [row for row in rows if row.status == status]
    if keyword:
        rows = [row for row in rows if keyword.lower() in f"{row.case_no} {row.summary_title or ''} {row.chief_complaint or ''}".lower()]
    start = (page - 1) * page_size
    items = rows[start : start + page_size]
    data = []
    for row in items:
        detail = build_consultation_detail(db, row, include_patient=True)
        data.append(
            {
                "case_id": detail["case_id"],
                "case_no": detail["case_no"],
                "summary_title": detail["summary_title"],
                "status": detail["status"],
                "risk_level": detail["risk_level"],
                "submitted_at": detail["submitted_at"],
                "patient": detail.get("patient"),
                "ai_result": detail["ai_result"],
                "doctor_reply": detail["doctor_reply"],
            }
        )
    return response_envelope(request, {"list": data, "total": len(rows), "page": page, "page_size": page_size})


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
    reply = ConsultationReply(
        consultation_id=case.id,
        doctor_id=doctor.id,
        content=payload.content,
        suggest_offline_visit=payload.suggest_offline_visit,
        suggest_follow_up=payload.suggest_follow_up,
        doctor_remark=payload.doctor_remark,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(reply)
    db.add(
        ConsultationMessage(
            consultation_id=case.id,
            sender_role="DOCTOR",
            sender_id=user.id,
            message_type="TEXT",
            content=payload.content,
            created_at=datetime.utcnow(),
        )
    )
    case.status = "DOCTOR_REPLIED"
    case.updated_at = datetime.utcnow()
    create_notification(
        db,
        case.user_id,
        "医生已回复问诊",
        f"问诊单 {case.case_no} 已收到医生建议，请及时查看。",
        "CONSULTATION",
        "CONSULTATION",
        case.id,
    )
    log_operation(db, user.id, user.role_type, "DOCTOR", "REPLY", str(case.id), f"回复问诊单 {case.case_no}", request.client.host if request.client else None)
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
    log_operation(db, user.id, user.role_type, "DOCTOR", "AI_FEEDBACK", str(case.id), f"提交 AI 反馈 {payload.ai_accuracy}", request.client.host if request.client else None)
    db.commit()
    return response_envelope(request, {"feedback_id": feedback.id}, "反馈已提交")


@router.get("/patients/{user_id}")
def patient_detail(user_id: int, request: Request, user: User = Depends(require_roles("DOCTOR")), db: Session = Depends(get_db)) -> dict:
    doctor = _current_doctor(user, db)
    rows = db.execute(
        select(Consultation).where(Consultation.assigned_doctor_id == doctor.id, Consultation.user_id == user_id, Consultation.is_deleted == 0).order_by(Consultation.created_at.desc())
    ).scalars().all()
    if not rows:
        raise HTTPException(status_code=404, detail="当前医生暂无该患者档案")
    detail = build_consultation_detail(db, rows[0], include_patient=True)
    return response_envelope(
        request,
        {
            "patient": detail["patient"],
            "recent_consultations": [
                {
                    "case_id": row.id,
                    "case_no": row.case_no,
                    "summary_title": row.summary_title,
                    "status": row.status,
                    "risk_level": row.risk_level,
                    "submitted_at": row.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if row.submitted_at else None,
                }
                for row in rows[:8]
            ],
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
    rows = db.execute(select(ConsultationReply).where(ConsultationReply.doctor_id == doctor.id).order_by(ConsultationReply.created_at.desc())).scalars().all()
    start = (page - 1) * page_size
    items = rows[start : start + page_size]
    consultations = {row.id: row for row in db.execute(select(Consultation)).scalars().all()}
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
                    "created_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for row in items
            ],
            "total": len(rows),
            "page": page,
            "page_size": page_size,
        },
    )
