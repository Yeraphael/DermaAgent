from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai import analyzer
from app.model import (
    AIAnalysisRecord,
    Consultation,
    ConsultationImage,
    ConsultationReply,
    Doctor,
    HealthProfile,
    KnowledgeChunkMetadata,
    KnowledgeDocument,
    Notification,
    OperationLog,
    User,
    UserProfile,
)


def paginate(items: list, page: int, page_size: int) -> dict:
    start = (page - 1) * page_size
    end = start + page_size
    return {"list": items[start:end], "total": len(items), "page": page, "page_size": page_size}


def log_operation(
    db: Session,
    account_id: int | None,
    role_type: str | None,
    module_name: str,
    operation_type: str,
    business_id: str | None,
    operation_desc: str,
    request_ip: str | None = None,
    operation_result: str = "SUCCESS",
) -> None:
    db.add(
        OperationLog(
            account_id=account_id,
            role_type=role_type,
            module_name=module_name,
            operation_type=operation_type,
            business_id=business_id,
            operation_desc=operation_desc,
            request_ip=request_ip,
            operation_result=operation_result,
            created_at=datetime.utcnow(),
        )
    )


def ensure_user_profile(db: Session, user_id: int) -> tuple[UserProfile, HealthProfile | None]:
    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
    if not profile:
        profile = UserProfile(user_id=user_id, real_name="", created_at=datetime.utcnow(), updated_at=datetime.utcnow())
        db.add(profile)
        db.flush()
    health = db.scalar(select(HealthProfile).where(HealthProfile.user_profile_id == profile.id))
    return profile, health


def serialize_account(user: User) -> dict:
    return {
        "account_id": user.id,
        "username": user.username,
        "role_type": user.role_type,
        "phone": user.phone,
        "email": user.email,
        "avatar_url": user.avatar_url,
        "status": user.status,
    }


def serialize_profile(user: User, profile: UserProfile | None) -> dict:
    return {
        "user_id": user.id,
        "real_name": profile.real_name if profile else "",
        "gender": profile.gender if profile else "",
        "age": profile.age if profile else None,
        "birthday": profile.birthday.isoformat() if profile and profile.birthday else None,
        "city": profile.city if profile else "",
        "occupation": profile.occupation if profile else "",
        "avatar_url": user.avatar_url,
        "phone": user.phone,
        "email": user.email,
        "emergency_contact": profile.emergency_contact if profile else "",
        "emergency_phone": profile.emergency_phone if profile else "",
        "remark": profile.remark if profile else "",
    }


def serialize_health(health: HealthProfile | None) -> dict:
    return {
        "allergy_history": health.allergy_history if health else "",
        "past_medical_history": health.past_medical_history if health else "",
        "medication_history": health.medication_history if health else "",
        "skin_type": health.skin_type if health else "",
        "skin_sensitivity": health.skin_sensitivity if health else "",
        "sleep_pattern": health.sleep_pattern if health else "",
        "diet_preference": health.diet_preference if health else "",
        "special_notes": health.special_notes if health else "",
    }


def select_doctor_for_case(db: Session) -> Doctor | None:
    doctors = db.execute(
        select(Doctor).join(User, Doctor.user_id == User.id).where(Doctor.audit_status == "APPROVED", Doctor.service_status == 1, User.status == 1)
    ).scalars().all()
    if not doctors:
        return None
    pending = {
        doctor.id: db.scalar(
            select(func.count(Consultation.id)).where(Consultation.assigned_doctor_id == doctor.id, Consultation.status == "WAIT_DOCTOR")
        )
        or 0
        for doctor in doctors
    }
    return sorted(doctors, key=lambda item: (pending.get(item.id, 0), item.id))[0]


def next_case_no(db: Session) -> str:
    total = db.scalar(select(func.count(Consultation.id))) or 0
    return f"CASE{datetime.utcnow().strftime('%Y%m%d')}{total + 1:04d}"


def health_summary(health: HealthProfile | None) -> str:
    if not health:
        return "未填写健康档案"
    return "；".join(
        filter(
            None,
            [
                f"肤质：{health.skin_type}" if health.skin_type else "",
                f"过敏史：{health.allergy_history}" if health.allergy_history else "",
                f"既往史：{health.past_medical_history}" if health.past_medical_history else "",
                f"备注：{health.special_notes}" if health.special_notes else "",
            ],
        )
    )


def latest_ai(db: Session, consultation_id: int) -> AIAnalysisRecord | None:
    return db.scalar(select(AIAnalysisRecord).where(AIAnalysisRecord.consultation_id == consultation_id).order_by(AIAnalysisRecord.created_at.desc()))


def latest_reply(db: Session, consultation_id: int) -> ConsultationReply | None:
    return db.scalar(select(ConsultationReply).where(ConsultationReply.consultation_id == consultation_id).order_by(ConsultationReply.created_at.desc()))


def build_ai_payload(record: AIAnalysisRecord | None) -> dict | None:
    if not record:
        return None
    return {
        "analysis_id": record.id,
        "model_name": record.model_name,
        "prompt_version": record.prompt_version,
        "image_observation": record.image_observation,
        "possible_conditions": record.possible_conditions,
        "risk_level": record.risk_level,
        "care_advice": record.care_advice,
        "hospital_advice": record.hospital_advice,
        "high_risk_alert": record.high_risk_alert,
        "disclaimer": record.disclaimer,
        "analysis_status": record.analysis_status,
        "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


def build_reply_payload(db: Session, reply: ConsultationReply | None) -> dict | None:
    if not reply:
        return None
    doctor = db.scalar(select(Doctor).where(Doctor.id == reply.doctor_id))
    return {
        "message_id": reply.id,
        "doctor_id": reply.doctor_id,
        "doctor_name": doctor.doctor_name if doctor else "",
        "content": reply.content,
        "suggest_offline_visit": reply.suggest_offline_visit,
        "suggest_follow_up": reply.suggest_follow_up,
        "doctor_remark": reply.doctor_remark,
        "created_at": reply.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


def build_consultation_detail(db: Session, consultation: Consultation, include_patient: bool = False) -> dict:
    user = db.scalar(select(User).where(User.id == consultation.user_id))
    profile, health = ensure_user_profile(db, consultation.user_id)
    doctor = db.scalar(select(Doctor).where(Doctor.id == consultation.assigned_doctor_id)) if consultation.assigned_doctor_id else None
    images = db.execute(select(ConsultationImage).where(ConsultationImage.consultation_id == consultation.id).order_by(ConsultationImage.sort_no.asc())).scalars().all()
    payload = {
        "case_id": consultation.id,
        "case_no": consultation.case_no,
        "summary_title": consultation.summary_title,
        "chief_complaint": consultation.chief_complaint,
        "onset_duration": consultation.onset_duration,
        "itch_level": consultation.itch_level,
        "pain_level": consultation.pain_level,
        "spread_flag": consultation.spread_flag,
        "status": consultation.status,
        "risk_level": consultation.risk_level,
        "need_doctor_review": consultation.need_doctor_review,
        "submitted_at": consultation.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if consultation.submitted_at else None,
        "images": [{"image_id": image.id, "file_url": image.file_url, "file_name": image.file_name} for image in images],
        "ai_result": build_ai_payload(latest_ai(db, consultation.id)),
        "doctor_reply": build_reply_payload(db, latest_reply(db, consultation.id)),
        "doctor": {
            "doctor_id": doctor.id,
            "doctor_name": doctor.doctor_name,
            "department": doctor.department,
            "title_name": doctor.title_name,
        }
        if doctor
        else None,
    }
    if include_patient and user:
        payload["patient"] = {
            "user": serialize_account(user),
            "profile": serialize_profile(user, profile),
            "health_profile": serialize_health(health),
        }
    return payload


def rerun_ai_analysis(db: Session, consultation: Consultation) -> AIAnalysisRecord:
    _, health = ensure_user_profile(db, consultation.user_id)
    images = db.execute(select(ConsultationImage).where(ConsultationImage.consultation_id == consultation.id).order_by(ConsultationImage.sort_no.asc())).scalars().all()
    result = analyzer.analyze(consultation.chief_complaint or "", [item.file_url for item in images], health_summary(health))
    record = AIAnalysisRecord(
        consultation_id=consultation.id,
        model_name=result.model_name,
        prompt_version=result.prompt_version,
        input_summary=f"{consultation.chief_complaint or ''} | {health_summary(health)}",
        image_observation=result.image_observation,
        possible_conditions=result.possible_conditions,
        risk_level=result.risk_level,
        care_advice=result.care_advice,
        hospital_advice=result.hospital_advice,
        high_risk_alert=result.high_risk_alert,
        disclaimer=result.disclaimer,
        raw_response=result.raw_response,
        analysis_status="SUCCESS",
        created_at=datetime.utcnow(),
    )
    consultation.risk_level = result.risk_level
    consultation.ai_confidence = 0.82 if result.risk_level == "LOW" else 0.73 if result.risk_level == "MEDIUM" else 0.67
    consultation.status = "WAIT_DOCTOR" if consultation.need_doctor_review or result.risk_level == "HIGH" else "AI_DONE"
    consultation.updated_at = datetime.utcnow()
    db.add(record)
    db.flush()
    return record


def create_notification(
    db: Session,
    user_id: int,
    title: str,
    content: str,
    notification_type: str,
    related_business_type: str | None,
    related_business_id: int | None,
) -> None:
    db.add(
        Notification(
            user_id=user_id,
            title=title,
            content=content,
            notification_type=notification_type,
            related_business_type=related_business_type,
            related_business_id=related_business_id,
            read_flag=0,
            created_at=datetime.utcnow(),
        )
    )


def rebuild_document_chunks(db: Session, document: KnowledgeDocument) -> int:
    existing = db.execute(select(KnowledgeChunkMetadata).where(KnowledgeChunkMetadata.document_id == document.id)).scalars().all()
    for item in existing:
        db.delete(item)
    chunks = [
        f"{document.doc_title} 提醒先识别诱因、发病部位与是否伴随瘙痒、疼痛、扩散。",
        f"{document.doc_title} 建议优先采用温和清洁、规律作息与减少刺激的基础护理策略。",
        f"{document.doc_title} 如果出现渗液、发热、破溃或反复不缓解，应尽快线下就医。",
        f"{document.doc_title} 就诊时建议携带近期照片、既往过敏史和用药情况，便于医生判断。",
    ]
    for index, text in enumerate(chunks, start=1):
        db.add(
            KnowledgeChunkMetadata(
                document_id=document.id,
                chunk_no=index,
                chunk_text=text,
                keywords="、".join(filter(None, [document.category or "", document.tag_list or "", document.doc_title])),
                token_count=len(text),
                enabled_flag=1,
                created_at=datetime.utcnow(),
            )
        )
    document.chunk_count = len(chunks)
    document.updated_at = datetime.utcnow()
    return len(chunks)
