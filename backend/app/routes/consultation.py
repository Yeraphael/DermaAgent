from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.middleware import response_envelope
from app.model import AIAnalysisRecord, Consultation, ConsultationImage, ConsultationMessage, User
from app.routes.deps import get_current_user, require_roles
from app.schema import AnalyzeIn, ConsultationCreateIn, ConsultationMessageIn
from app.service import (
    build_ai_payload,
    build_consultation_detail,
    create_notification,
    log_operation,
    next_case_no,
    rerun_ai_analysis,
    select_doctor_for_case,
)


router = APIRouter()


def _load_case(db: Session, case_id: int) -> Consultation | None:
    return db.scalar(select(Consultation).where(Consultation.id == case_id, Consultation.is_deleted == 0))


def _ensure_case_access(db: Session, case_id: int, user: User) -> Consultation:
    case = _load_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="问诊单不存在")

    if user.role_type == "ADMIN":
        return case

    if user.role_type == "USER" and case.user_id != user.id:
        raise HTTPException(status_code=403, detail="无权查看该问诊单")

    if user.role_type == "DOCTOR":
        from app.model import Doctor

        doctor_profile = db.scalar(select(Doctor).where(Doctor.user_id == user.id))
        if case.assigned_doctor_id is None:
            raise HTTPException(status_code=403, detail="该问诊单尚未分配给医生")
        if not doctor_profile or doctor_profile.id != case.assigned_doctor_id:
            raise HTTPException(status_code=403, detail="无权查看该问诊单")

    return case


@router.post("/consultations")
def create_consultation(
    payload: ConsultationCreateIn,
    request: Request,
    user: User = Depends(require_roles("USER")),
    db: Session = Depends(get_db),
) -> dict:
    if not payload.image_urls:
        raise HTTPException(status_code=400, detail="图文问诊至少需要上传 1 张图片")
    if len(payload.image_urls) > 5:
        raise HTTPException(status_code=400, detail="单次问诊最多上传 5 张图片")

    assigned = select_doctor_for_case(db)
    title = payload.chief_complaint[:24] if payload.chief_complaint else "皮肤健康咨询"
    case = Consultation(
        case_no=next_case_no(db),
        user_id=user.id,
        assigned_doctor_id=assigned.id if assigned else None,
        summary_title=title,
        chief_complaint=payload.chief_complaint,
        onset_duration=payload.onset_duration,
        itch_level=payload.itch_level,
        pain_level=payload.pain_level,
        spread_flag=payload.spread_flag,
        status="PENDING_AI",
        need_doctor_review=payload.need_doctor_review,
        ai_enabled=1,
        submitted_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        is_deleted=0,
    )
    db.add(case)
    db.flush()

    for index, image_url in enumerate(payload.image_urls, start=1):
        db.add(
            ConsultationImage(
                consultation_id=case.id,
                file_name=image_url.rsplit("/", 1)[-1],
                file_url=image_url,
                file_type="image",
                sort_no=index,
                uploaded_at=datetime.utcnow(),
            )
        )

    db.add(
        ConsultationMessage(
            consultation_id=case.id,
            sender_role="USER",
            sender_id=user.id,
            message_type="TEXT",
            content=payload.chief_complaint or "用户提交了图文问诊",
            created_at=datetime.utcnow(),
        )
    )

    record = rerun_ai_analysis(db, case)
    if not case.assigned_doctor_id and case.status == "WAIT_DOCTOR":
        assigned = select_doctor_for_case(db)
        case.assigned_doctor_id = assigned.id if assigned else None

    create_notification(
        db,
        user.id,
        "问诊已受理",
        f"问诊单 {case.case_no} 已生成，可查看智能图文辅助分析结果。",
        "CONSULTATION",
        "CONSULTATION",
        case.id,
    )

    if case.assigned_doctor_id:
        from app.model import Doctor

        doctor = db.scalar(select(Doctor).where(Doctor.id == case.assigned_doctor_id))
        if doctor:
            create_notification(
                db,
                doctor.user_id,
                "新的待处理问诊",
                f"问诊单 {case.case_no} 已分配给你，请查看并给出专业建议。",
                "CONSULTATION",
                "CONSULTATION",
                case.id,
            )

    log_operation(
        db,
        user.id,
        user.role_type,
        "CONSULTATION",
        "CREATE",
        str(case.id),
        f"创建问诊单 {case.case_no}",
        request.client.host if request.client else None,
    )
    db.commit()
    return response_envelope(
        request,
        {
            "consultation": build_consultation_detail(db, case),
            "ai_result": build_ai_payload(record),
        },
        "问诊提交成功",
    )


@router.get("/consultations/my")
def my_consultations(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    status: str | None = Query(default=None),
    user: User = Depends(require_roles("USER")),
    db: Session = Depends(get_db),
) -> dict:
    rows = db.execute(
        select(Consultation)
        .where(Consultation.user_id == user.id, Consultation.is_deleted == 0)
        .order_by(Consultation.created_at.desc())
    ).scalars().all()
    if status:
        rows = [row for row in rows if row.status == status]

    start = (page - 1) * page_size
    items = rows[start : start + page_size]
    data = []
    for row in items:
        detail = build_consultation_detail(db, row)
        data.append(
            {
                "case_id": detail["case_id"],
                "case_no": detail["case_no"],
                "summary_title": detail["summary_title"],
                "status": detail["status"],
                "risk_level": detail["risk_level"],
                "need_doctor_review": detail["need_doctor_review"],
                "submitted_at": detail["submitted_at"],
                "ai_result": detail["ai_result"],
                "doctor_reply": detail["doctor_reply"],
            }
        )
    return response_envelope(request, {"list": data, "total": len(rows), "page": page, "page_size": page_size})


@router.get("/consultations/{case_id}")
def consultation_detail(
    case_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    case = _ensure_case_access(db, case_id, user)
    return response_envelope(request, build_consultation_detail(db, case, include_patient=user.role_type in {"DOCTOR", "ADMIN"}))


@router.get("/consultations/{case_id}/messages")
def consultation_messages(
    case_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    _ensure_case_access(db, case_id, user)
    rows = db.execute(
        select(ConsultationMessage)
        .where(ConsultationMessage.consultation_id == case_id)
        .order_by(ConsultationMessage.created_at.asc())
    ).scalars().all()
    return response_envelope(
        request,
        [
            {
                "message_id": row.id,
                "sender_role": row.sender_role,
                "sender_id": row.sender_id,
                "message_type": row.message_type,
                "content": row.content,
                "created_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for row in rows
        ],
    )


@router.post("/consultations/{case_id}/messages")
def send_consultation_message(
    case_id: int,
    payload: ConsultationMessageIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    case = _ensure_case_access(db, case_id, user)
    message = ConsultationMessage(
        consultation_id=case.id,
        sender_role=user.role_type,
        sender_id=user.id,
        message_type=payload.message_type,
        content=payload.content,
        created_at=datetime.utcnow(),
    )
    db.add(message)
    case.updated_at = datetime.utcnow()

    target_user_id = None
    if user.role_type == "USER" and case.assigned_doctor_id:
        from app.model import Doctor

        doctor = db.scalar(select(Doctor).where(Doctor.id == case.assigned_doctor_id))
        target_user_id = doctor.user_id if doctor else None
    elif user.role_type == "DOCTOR":
        target_user_id = case.user_id

    if target_user_id:
        create_notification(
            db,
            target_user_id,
            "问诊新消息",
            f"问诊单 {case.case_no} 有新的沟通消息。",
            "CONSULTATION",
            "CONSULTATION",
            case.id,
        )

    log_operation(
        db,
        user.id,
        user.role_type,
        "CONSULTATION",
        "MESSAGE",
        str(case.id),
        f"发送问诊消息 {payload.message_type}",
        request.client.host if request.client else None,
    )
    db.commit()
    return response_envelope(request, {"message_id": message.id}, "发送成功")


@router.post("/consultations/{case_id}/close")
def close_consultation(
    case_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    case = _ensure_case_access(db, case_id, user)
    case.status = "CLOSED"
    case.closed_at = datetime.utcnow()
    case.updated_at = datetime.utcnow()
    create_notification(
        db,
        case.user_id,
        "问诊已结束",
        f"问诊单 {case.case_no} 已关闭，如症状持续请重新发起问诊或线下就医。",
        "CONSULTATION",
        "CONSULTATION",
        case.id,
    )
    log_operation(
        db,
        user.id,
        user.role_type,
        "CONSULTATION",
        "CLOSE",
        str(case.id),
        f"关闭问诊单 {case.case_no}",
        request.client.host if request.client else None,
    )
    db.commit()
    return response_envelope(request, {"case_id": case.id, "status": case.status}, "已关闭")


@router.post("/ai/consultations/{case_id}/analyze")
def analyze_consultation(
    case_id: int,
    payload: AnalyzeIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    case = _ensure_case_access(db, case_id, user)
    if case.status == "PENDING_AI" or payload.force_reanalyze:
        record = rerun_ai_analysis(db, case)
        log_operation(
            db,
            user.id,
            user.role_type,
            "AI",
            "ANALYZE",
            str(case.id),
            f"执行 AI 分析 {case.case_no}",
            request.client.host if request.client else None,
        )
        db.commit()
        return response_envelope(request, build_ai_payload(record), "分析完成")

    latest = db.scalar(
        select(AIAnalysisRecord)
        .where(AIAnalysisRecord.consultation_id == case.id)
        .order_by(AIAnalysisRecord.created_at.desc())
    )
    return response_envelope(request, build_ai_payload(latest), "已返回最新分析结果")


@router.get("/ai/consultations/{case_id}/result")
def analyze_result(
    case_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    case = _ensure_case_access(db, case_id, user)
    latest = db.scalar(
        select(AIAnalysisRecord)
        .where(AIAnalysisRecord.consultation_id == case.id)
        .order_by(AIAnalysisRecord.created_at.desc())
    )
    return response_envelope(request, build_ai_payload(latest))


@router.post("/ai/consultations/{case_id}/retry")
def retry_analyze(
    case_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    case = _ensure_case_access(db, case_id, user)
    record = rerun_ai_analysis(db, case)
    log_operation(
        db,
        user.id,
        user.role_type,
        "AI",
        "RETRY",
        str(case.id),
        f"重新分析问诊单 {case.case_no}",
        request.client.host if request.client else None,
    )
    db.commit()
    return response_envelope(request, build_ai_payload(record), "重新分析完成")
