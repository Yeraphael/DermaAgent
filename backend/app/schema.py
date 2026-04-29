from __future__ import annotations

from pydantic import BaseModel, Field


class LoginIn(BaseModel):
    username: str
    password: str


class VerificationCodeSendIn(BaseModel):
    phone: str = Field(min_length=6, max_length=20)
    scene: str = "REGISTER"


class RegisterIn(BaseModel):
    username: str
    verification_code: str | None = None
    password: str = Field(min_length=8)
    confirm_password: str = Field(min_length=8)
    phone: str | None = None
    email: str | None = None
    role_type: str = "USER"


class PasswordResetIn(BaseModel):
    phone: str = Field(min_length=6, max_length=20)
    code: str = Field(min_length=4, max_length=8)
    new_password: str = Field(min_length=8)
    confirm_password: str = Field(min_length=8)


class PasswordChangeIn(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)
    confirm_password: str = Field(min_length=8)


class ProfileUpdateIn(BaseModel):
    real_name: str | None = None
    gender: str | None = None
    age: int | None = None
    birthday: str | None = None
    city: str | None = None
    occupation: str | None = None
    avatar_url: str | None = None
    emergency_contact: str | None = None
    emergency_phone: str | None = None
    remark: str | None = None


class HealthProfileUpdateIn(BaseModel):
    allergy_history: str | None = None
    past_medical_history: str | None = None
    medication_history: str | None = None
    skin_type: str | None = None
    skin_sensitivity: str | None = None
    sleep_pattern: str | None = None
    diet_preference: str | None = None
    special_notes: str | None = None


class ConsultationCreateIn(BaseModel):
    chief_complaint: str = ""
    onset_duration: str | None = None
    itch_level: int = 0
    pain_level: int = 0
    spread_flag: int = 0
    need_doctor_review: int = 1
    image_urls: list[str] = Field(default_factory=list)


class ConsultationMessageIn(BaseModel):
    message_type: str = "TEXT"
    content: str


class AnalyzeIn(BaseModel):
    force_reanalyze: bool = False


class ChatSessionCreateIn(BaseModel):
    title: str | None = Field(default=None, max_length=120)


class ChatMessageCreateIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class DoctorReplyIn(BaseModel):
    content: str
    suggest_offline_visit: int = 0
    suggest_follow_up: int = 0
    doctor_remark: str | None = None


class DoctorAIFeedbackIn(BaseModel):
    ai_accuracy: str
    correction_note: str | None = None
    knowledge_gap_note: str | None = None


class StatusUpdateIn(BaseModel):
    status: int


class AuditUpdateIn(BaseModel):
    audit_status: str
    audit_remark: str | None = None


class ConfigUpdateIn(BaseModel):
    config_value: str


class AnnouncementIn(BaseModel):
    title: str
    content: str
    publish_scope: str = "ALL"
    status: int = 1
