from fastapi import APIRouter

from app.routes import admin, auth, chat, common, consultation, doctor, user


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(common.router, tags=["公共"])
api_router.include_router(chat.router, prefix="/chat", tags=["文本问答"])
api_router.include_router(user.router, prefix="/user", tags=["用户"])
api_router.include_router(consultation.router, tags=["问诊"])
api_router.include_router(doctor.router, prefix="/doctor", tags=["医生"])
api_router.include_router(admin.router, prefix="/admin", tags=["管理员"])
