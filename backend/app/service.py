from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai import analyzer
from app.model import (
    AIAnalysisRecord,
    Consultation,
    ConsultationImage,
    ConsultationReply,
    Doctor,
    DoctorAIFeedback,
    Notification,
    OperationLog,
    SystemConfig,
    User,
    UserProfile,
    HealthProfile,
)


CONFIG_DEFAULTS: dict[str, dict[str, str]] = {
    "ai.mode": {"value": "mock", "group": "AI_MODEL", "description": "AI 调用模式"},
    "ai.visual_model": {"value": "mock-qwen-vl", "group": "AI_MODEL", "description": "图文问诊模型"},
    "ai.text_model": {"value": "qwen-plus", "group": "AI_MODEL", "description": "文本问答模型"},
    "ai.temperature": {"value": "0.2", "group": "AI_MODEL", "description": "模型温度"},
    "ai.max_tokens": {"value": "1200", "group": "AI_MODEL", "description": "最大输出长度"},
    "ai.timeout_seconds": {"value": "30", "group": "AI_MODEL", "description": "请求超时时间"},
    "prompt.consultation_analysis": {
        "value": (
            "你是一名皮肤科图文问诊分析助手。请结合用户上传图片、症状描述和健康档案，"
            "输出图像观察、可能方向、风险等级、护理建议和是否建议线下就医。"
        ),
        "group": "PROMPT",
        "description": "图文问诊分析提示词模板",
    },
    "prompt.qa_assistant": {
        "value": "你是一名谨慎、专业的皮肤健康问答助手，优先给出清晰建议并提醒必要时线下就医。",
        "group": "PROMPT",
        "description": "知识问答提示词模板",
    },
    "risk.rules": {
        "value": json.dumps(
            {
                "low": {"label": "低风险", "range": [0, 29], "action": "居家护理"},
                "medium": {"label": "中风险", "range": [30, 69], "action": "建议医生复核"},
                "high": {"label": "高风险", "range": [70, 100], "action": "建议尽快线下就医"},
            },
            ensure_ascii=False,
        ),
        "group": "RISK",
        "description": "风险等级规则",
    },
    "upload.rules": {
        "value": json.dumps(
            {"max_count": 6, "max_mb": 10, "formats": ["jpg", "jpeg", "png", "webp"]},
            ensure_ascii=False,
        ),
        "group": "UPLOAD",
        "description": "图片上传限制",
    },
    "notice.rules": {
        "value": json.dumps(
            {
                "doctor_reply_notice": True,
                "high_risk_notice": True,
                "analysis_finish_notice": True,
            },
            ensure_ascii=False,
        ),
        "group": "NOTICE",
        "description": "通知规则",
    },
    "permission.role_matrix": {
        "value": json.dumps(
            {
                "USER": ["consultation:create", "consultation:view:self", "profile:update:self"],
                "DOCTOR": [
                    "doctor:dashboard",
                    "doctor:consultation:reply",
                    "doctor:patient:view",
                    "doctor:ai_feedback:create",
                ],
                "ADMIN": [
                    "admin:dashboard",
                    "admin:user:manage",
                    "admin:doctor:audit",
                    "admin:consultation:manage",
                    "admin:config:manage",
                    "admin:logs:view",
                ],
            },
            ensure_ascii=False,
        ),
        "group": "PERMISSION",
        "description": "角色权限配置",
    },
}


def paginate(items: list[Any], page: int, page_size: int) -> dict[str, Any]:
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


def serialize_account(user: User | None) -> dict:
    if not user:
        return {}
    return {
        "account_id": user.id,
        "username": user.username,
        "role_type": user.role_type,
        "phone": user.phone,
        "email": user.email,
        "avatar_url": user.avatar_url,
        "status": user.status,
        "last_login_at": user.last_login_at.strftime("%Y-%m-%d %H:%M:%S") if user.last_login_at else None,
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
        "updated_at": health.updated_at.strftime("%Y-%m-%d %H:%M:%S") if health and health.updated_at else None,
    }


def upsert_default_system_configs(db: Session, updated_by: int | None = None) -> None:
    existing = {
        row.config_key: row
        for row in db.execute(select(SystemConfig).where(SystemConfig.config_key.in_(tuple(CONFIG_DEFAULTS.keys())))).scalars().all()
    }
    now = datetime.utcnow()
    changed = False
    for key, meta in CONFIG_DEFAULTS.items():
        if key in existing:
            continue
        db.add(
            SystemConfig(
                config_key=key,
                config_value=meta["value"],
                config_group=meta["group"],
                description=meta["description"],
                updated_by=updated_by,
                updated_at=now,
            )
        )
        changed = True
    if changed:
        db.flush()


def get_config_map(db: Session, ensure_defaults: bool = True) -> dict[str, str]:
    if ensure_defaults:
        upsert_default_system_configs(db)
    rows = db.execute(select(SystemConfig)).scalars().all()
    return {row.config_key: row.config_value for row in rows}


def split_text_segments(value: str | None) -> list[str]:
    if not value:
        return []
    items = [
        segment.strip(" \t\r\n-•0123456789.、")
        for segment in re.split(r"[\r\n]+|[；;]", value)
        if segment.strip()
    ]
    return [item for item in items if item]


def get_bool_config(config_map: dict[str, str], key: str, default: bool = False) -> bool:
    value = config_map.get(key)
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def get_int_config(config_map: dict[str, str], key: str, default: int) -> int:
    value = config_map.get(key)
    if value is None:
        return default
    try:
        return int(float(str(value).strip()))
    except ValueError:
        return default


def get_float_config(config_map: dict[str, str], key: str, default: float) -> float:
    value = config_map.get(key)
    if value is None:
        return default
    try:
        return float(str(value).strip())
    except ValueError:
        return default


def get_json_config(config_map: dict[str, str], key: str, default: Any) -> Any:
    value = config_map.get(key)
    if value is None:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def select_doctor_for_case(db: Session) -> Doctor | None:
    config_map = get_config_map(db)
    if not get_bool_config(config_map, "consultation.auto_assign", True):
        return None

    doctors = db.execute(
        select(Doctor).join(User, Doctor.user_id == User.id).where(
            Doctor.audit_status == "APPROVED",
            Doctor.service_status == 1,
            User.status == 1,
            User.is_deleted == 0,
        )
    ).scalars().all()
    if not doctors:
        return None

    pending = {
        doctor.id: db.scalar(
            select(func.count(Consultation.id)).where(
                Consultation.assigned_doctor_id == doctor.id,
                Consultation.status == "WAIT_DOCTOR",
                Consultation.is_deleted == 0,
            )
        )
        or 0
        for doctor in doctors
    }
    return sorted(doctors, key=lambda item: (pending.get(item.id, 0), item.id))[0]


def next_case_no(db: Session) -> str:
    total = db.scalar(select(func.count(Consultation.id)).where(Consultation.is_deleted == 0)) or 0
    return f"{datetime.utcnow().strftime('%Y-%m%d')}-{total + 1:06d}"


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
                f"长期用药：{health.medication_history}" if health.medication_history else "",
                f"生活习惯：{health.sleep_pattern}/{health.diet_preference}"
                if health.sleep_pattern or health.diet_preference
                else "",
                f"备注：{health.special_notes}" if health.special_notes else "",
            ],
        )
    )


def latest_ai(db: Session, consultation_id: int) -> AIAnalysisRecord | None:
    return db.scalar(
        select(AIAnalysisRecord)
        .where(AIAnalysisRecord.consultation_id == consultation_id)
        .order_by(AIAnalysisRecord.created_at.desc(), AIAnalysisRecord.id.desc())
    )


def latest_reply(db: Session, consultation_id: int) -> ConsultationReply | None:
    return db.scalar(
        select(ConsultationReply)
        .where(ConsultationReply.consultation_id == consultation_id)
        .order_by(ConsultationReply.created_at.desc(), ConsultationReply.id.desc())
    )


def latest_ai_feedback(db: Session, consultation_id: int) -> DoctorAIFeedback | None:
    return db.scalar(
        select(DoctorAIFeedback)
        .where(DoctorAIFeedback.consultation_id == consultation_id)
        .order_by(DoctorAIFeedback.created_at.desc(), DoctorAIFeedback.id.desc())
    )


def build_ai_payload(record: AIAnalysisRecord | None) -> dict | None:
    if not record:
        return None
    return {
        "analysis_id": record.id,
        "model_name": record.model_name,
        "prompt_version": record.prompt_version,
        "image_observation": record.image_observation,
        "possible_conditions": record.possible_conditions,
        "possible_conditions_list": split_text_segments(record.possible_conditions),
        "risk_level": record.risk_level,
        "care_advice": record.care_advice,
        "care_advice_list": split_text_segments(record.care_advice),
        "hospital_advice": record.hospital_advice,
        "high_risk_alert": record.high_risk_alert,
        "disclaimer": record.disclaimer,
        "analysis_status": record.analysis_status,
        "fail_reason": record.fail_reason,
        "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


def build_reply_content(first_impression: str | None, care_advice: str | None, doctor_remark: str | None, fallback: str | None) -> str:
    sections = []
    if first_impression:
        sections.append(first_impression.strip())
    if care_advice:
        sections.append(f"护理建议：{care_advice.strip()}")
    if doctor_remark:
        sections.append(f"医生备注：{doctor_remark.strip()}")
    if sections:
        return "\n\n".join(sections)
    return (fallback or "").strip()


def build_reply_payload(db: Session, reply: ConsultationReply | None) -> dict | None:
    if not reply:
        return None
    doctor = db.scalar(select(Doctor).where(Doctor.id == reply.doctor_id))
    return {
        "message_id": reply.id,
        "doctor_id": reply.doctor_id,
        "doctor_name": doctor.doctor_name if doctor else "",
        "content": reply.content,
        "first_impression": reply.first_impression,
        "care_advice": reply.care_advice,
        "suggest_offline_visit": reply.suggest_offline_visit,
        "suggest_follow_up": reply.suggest_follow_up,
        "doctor_remark": reply.doctor_remark,
        "created_at": reply.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": reply.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


def build_ai_feedback_payload(feedback: DoctorAIFeedback | None) -> dict | None:
    if not feedback:
        return None
    return {
        "feedback_id": feedback.id,
        "doctor_id": feedback.doctor_id,
        "ai_accuracy": feedback.ai_accuracy,
        "correction_note": feedback.correction_note,
        "knowledge_gap_note": feedback.knowledge_gap_note,
        "created_at": feedback.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


def build_patient_tags(health: HealthProfile | None, latest_case: Consultation | None = None) -> list[str]:
    tags: list[str] = []
    if health and health.skin_type:
        tags.append(health.skin_type)
    if health and health.skin_sensitivity:
        tags.append(health.skin_sensitivity)
    if health and health.allergy_history:
        tags.append("过敏史")
    if health and health.medication_history:
        tags.append("长期用药")
    if latest_case and latest_case.risk_level == "HIGH":
        tags.append("高风险随访")
    if latest_case and latest_case.summary_title:
        tags.append(latest_case.summary_title[:12])
    return tags[:4]


def calculate_health_score(health: HealthProfile | None, cases: list[Consultation]) -> int:
    score = 65
    if health:
        score += sum(
            4
            for value in [
                health.skin_type,
                health.skin_sensitivity,
                health.allergy_history,
                health.past_medical_history,
                health.medication_history,
                health.sleep_pattern,
                health.diet_preference,
            ]
            if value
        )
    score -= len([case for case in cases if case.risk_level == "HIGH"]) * 4
    score -= len([case for case in cases if case.risk_level == "MEDIUM"]) * 2
    if cases and cases[0].status == "DOCTOR_REPLIED":
        score += 3
    return max(48, min(score, 96))


def build_consultation_timeline(db: Session, consultation: Consultation) -> list[dict[str, str]]:
    timeline: list[dict[str, str]] = []
    if consultation.submitted_at:
        timeline.append(
            {
                "event": "SUBMITTED",
                "label": "用户提交问诊",
                "time": consultation.submitted_at.strftime("%Y-%m-%d %H:%M:%S"),
                "note": consultation.summary_title or consultation.chief_complaint or "",
            }
        )

    ai_record = latest_ai(db, consultation.id)
    if ai_record:
        timeline.append(
            {
                "event": "AI_ANALYZED",
                "label": "AI 分析完成",
                "time": ai_record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "note": ai_record.risk_level or ai_record.analysis_status,
            }
        )

    reply = latest_reply(db, consultation.id)
    if reply:
        timeline.append(
            {
                "event": "DOCTOR_REPLIED",
                "label": "医生已回复",
                "time": reply.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "note": (reply.first_impression or reply.content or "")[:80],
            }
        )

    feedback = latest_ai_feedback(db, consultation.id)
    if feedback:
        timeline.append(
            {
                "event": "AI_FEEDBACK",
                "label": "医生反馈 AI 结果",
                "time": feedback.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "note": feedback.ai_accuracy or "",
            }
        )

    if consultation.abnormal_flag and consultation.updated_at:
        timeline.append(
            {
                "event": "FLAGGED",
                "label": "管理员标记异常",
                "time": consultation.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                "note": consultation.abnormal_note or "已标记异常",
            }
        )

    if consultation.archived_flag and consultation.archived_at:
        timeline.append(
            {
                "event": "ARCHIVED",
                "label": "咨询已归档",
                "time": consultation.archived_at.strftime("%Y-%m-%d %H:%M:%S"),
                "note": "已从运营处理中归档",
            }
        )

    if consultation.closed_at:
        timeline.append(
            {
                "event": "CLOSED",
                "label": "咨询已结束",
                "time": consultation.closed_at.strftime("%Y-%m-%d %H:%M:%S"),
                "note": "当前问诊流程已关闭",
            }
        )

    return sorted(timeline, key=lambda item: item["time"])


def build_consultation_detail(db: Session, consultation: Consultation, include_patient: bool = False) -> dict:
    user = db.scalar(select(User).where(User.id == consultation.user_id))
    profile, health = ensure_user_profile(db, consultation.user_id)
    doctor = db.scalar(select(Doctor).where(Doctor.id == consultation.assigned_doctor_id)) if consultation.assigned_doctor_id else None
    images = db.execute(
        select(ConsultationImage)
        .where(ConsultationImage.consultation_id == consultation.id)
        .order_by(ConsultationImage.sort_no.asc(), ConsultationImage.id.asc())
    ).scalars().all()

    payload: dict[str, Any] = {
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
        "ai_confidence": consultation.ai_confidence,
        "submitted_at": consultation.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if consultation.submitted_at else None,
        "closed_at": consultation.closed_at.strftime("%Y-%m-%d %H:%M:%S") if consultation.closed_at else None,
        "abnormal_flag": consultation.abnormal_flag,
        "abnormal_note": consultation.abnormal_note,
        "archived_flag": consultation.archived_flag,
        "archived_at": consultation.archived_at.strftime("%Y-%m-%d %H:%M:%S") if consultation.archived_at else None,
        "images": [{"image_id": image.id, "file_url": image.file_url, "file_name": image.file_name} for image in images],
        "ai_result": build_ai_payload(latest_ai(db, consultation.id)),
        "doctor_reply": build_reply_payload(db, latest_reply(db, consultation.id)),
        "ai_feedback": build_ai_feedback_payload(latest_ai_feedback(db, consultation.id)),
        "doctor": {
            "doctor_id": doctor.id,
            "doctor_name": doctor.doctor_name,
            "department": doctor.department,
            "title_name": doctor.title_name,
            "hospital_name": doctor.hospital_name,
        }
        if doctor
        else None,
        "timeline": build_consultation_timeline(db, consultation),
    }

    if include_patient and user:
        patient_cases = db.execute(
            select(Consultation)
            .where(Consultation.user_id == user.id, Consultation.is_deleted == 0)
            .order_by(Consultation.created_at.desc(), Consultation.id.desc())
        ).scalars().all()
        payload["patient"] = {
            "account": serialize_account(user),
            "profile": serialize_profile(user, profile),
            "health_profile": serialize_health(health),
            "tags": build_patient_tags(health, patient_cases[0] if patient_cases else None),
            "health_score": calculate_health_score(health, patient_cases),
        }
    return payload


def rerun_ai_analysis(db: Session, consultation: Consultation) -> AIAnalysisRecord:
    _, health = ensure_user_profile(db, consultation.user_id)
    images = db.execute(
        select(ConsultationImage)
        .where(ConsultationImage.consultation_id == consultation.id)
        .order_by(ConsultationImage.sort_no.asc(), ConsultationImage.id.asc())
    ).scalars().all()
    config_map = get_config_map(db)
    runtime_config = {
        "ai_mode": config_map.get("ai.mode"),
        "visual_model": config_map.get("ai.visual_model"),
        "text_model": config_map.get("ai.text_model"),
        "temperature": get_float_config(config_map, "ai.temperature", 0.2),
        "max_tokens": get_int_config(config_map, "ai.max_tokens", 1200),
        "timeout_seconds": get_int_config(config_map, "ai.timeout_seconds", 30),
        "consultation_prompt": config_map.get("prompt.consultation_analysis"),
    }
    result = analyzer.analyze(consultation.chief_complaint or "", [item.file_url for item in images], health_summary(health), runtime_config)
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
        analysis_status=result.analysis_status,
        fail_reason=result.fail_reason,
        created_at=datetime.utcnow(),
    )
    consultation.risk_level = result.risk_level
    consultation.ai_confidence = 0.9 if result.risk_level == "LOW" else 0.78 if result.risk_level == "MEDIUM" else 0.66
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


def compute_accuracy_score(items: list[str]) -> float:
    if not items:
        return 0
    score = 0.0
    for item in items:
        if item == "ACCURATE":
            score += 1
        elif item == "PARTIAL":
            score += 0.6
        elif item == "INACCURATE":
            score += 0.2
    return round(score / len(items) * 100, 1)


def group_daily_counts(values: list[datetime], total_days: int = 7, anchor: date | None = None) -> list[dict[str, Any]]:
    end_date = anchor or datetime.utcnow().date()
    dates = [end_date - timedelta(days=offset) for offset in range(total_days - 1, -1, -1)]
    counts: dict[date, int] = {item: 0 for item in dates}
    for value in values:
        current = value.date()
        if current in counts:
            counts[current] += 1
    return [{"date": item, "count": counts[item]} for item in dates]
