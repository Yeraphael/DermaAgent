from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.middleware import RequestContextMiddleware
from app.router import api_router


settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(settings.upload_path)), name="uploads")
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/")
def healthcheck() -> dict:
    return {"app": settings.app_name, "status": "ok", "api_prefix": settings.api_prefix}
