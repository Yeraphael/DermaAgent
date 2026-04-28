from __future__ import annotations

import base64
import json
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse

import httpx

from app.config import get_settings


settings = get_settings()
DEFAULT_DISCLAIMER = "医疗辅助免责声明：本结果仅供健康参考，不能替代医生面诊与医学诊断。"
DEFAULT_HIGH_RISK_ALERT = "高风险就医提醒：如出现明显加重、发热、流脓或范围迅速扩大，请尽快线下就医。"


@dataclass
class AIResult:
    model_name: str
    prompt_version: str
    image_observation: str
    possible_conditions: str
    risk_level: str
    care_advice: str
    hospital_advice: str
    high_risk_alert: str
    disclaimer: str
    raw_response: str


class VisualAnalyzer:
    def analyze(self, complaint: str, image_urls: list[str], health_summary: str) -> AIResult:
        if settings.ai_mode.lower() == "real" and settings.qwen_api_key and settings.qwen_base_url:
            try:
                return self._real_call(complaint, image_urls, health_summary)
            except Exception as exc:  # noqa: BLE001
                return self._mock_call(complaint, image_urls, health_summary, fallback_reason=str(exc))
        return self._mock_call(complaint, image_urls, health_summary)

    def _mock_call(
        self,
        complaint: str,
        image_urls: list[str],
        health_summary: str,
        fallback_reason: str | None = None,
    ) -> AIResult:
        text = f"{complaint} {health_summary}".lower()
        risk = "LOW"
        image_observation = "上传图片显示局部炎症性皮损，整体更偏向轻中度的皮肤屏障受损或刺激后反应。"
        possible_conditions = "接触性皮炎\n湿疹样改变\n屏障受损"
        care_advice = "减少刺激和过度清洁\n优先使用温和保湿修护产品\n持续加重时及时线下就医"
        hospital_advice = "如果 3 到 5 天内持续加重、反复发作或影响睡眠，建议预约皮肤科面诊。"
        high_risk_alert = DEFAULT_HIGH_RISK_ALERT

        if any(keyword in text for keyword in ["pimple", "acne", "丘疹", "痘"]):
            image_observation = "图文信息更偏向炎症性丘疹或痤疮相关改变，暂未见到需要立即急诊处理的危险信号。"
            possible_conditions = "痤疮倾向\n毛囊炎\n油脂分泌相关皮损"
            care_advice = "不要频繁挤压皮损\n减少高糖高油饮食与熬夜\n保持温和清洁与轻量保湿"
        elif any(keyword in text for keyword in ["itch", "allergy", "red", "红", "痒", "过敏", "刺痛"]):
            risk = "MEDIUM"
            image_observation = "图文信息提示炎症性泛红和瘙痒表现，较符合接触刺激或过敏后屏障受损。"
            possible_conditions = "接触性皮炎\n过敏性皮炎\n湿疹样改变"
            care_advice = "暂停近期新增护肤和彩妆产品\n冷敷并加强无香精保湿\n避免热水和反复摩擦"
            hospital_advice = "如果夜间瘙痒明显、红斑持续扩大或刺痛加重，建议尽快面诊。"
        elif any(keyword in text for keyword in ["ooze", "pus", "fever", "blister", "worse", "渗液", "化脓", "发热", "水疱", "扩散"]):
            risk = "HIGH"
            image_observation = "图文信息提示皮损活动度较高，可能伴有破溃、渗出或继发感染风险。"
            possible_conditions = "中重度炎症性皮损\n继发感染风险\n需要进一步面诊评估"
            care_advice = "保持患处清洁干燥\n避免自行挤压、抓挠或叠加强刺激药物\n尽快到皮肤科进一步检查"
            hospital_advice = "建议尽快前往皮肤科或综合医院门诊，由医生进行面对面评估。"

        raw_payload = {
            "mode": "mock",
            "fallback_reason": fallback_reason,
            "complaint": complaint,
            "images": len(image_urls),
            "health_summary": health_summary,
        }
        model_name = f"mock-fallback-{settings.qwen_visual_model}" if fallback_reason else "mock-qwen-vl"
        return AIResult(
            model_name=model_name,
            prompt_version="consultation-v1",
            image_observation=image_observation,
            possible_conditions=possible_conditions,
            risk_level=risk,
            care_advice=care_advice,
            hospital_advice=hospital_advice,
            high_risk_alert=high_risk_alert,
            disclaimer=DEFAULT_DISCLAIMER,
            raw_response=json.dumps(raw_payload, ensure_ascii=False),
        )

    def _real_call(self, complaint: str, image_urls: list[str], health_summary: str) -> AIResult:
        prompt = "\n".join(
            [
                "你是皮肤健康图文问诊辅助分析助手。",
                "请结合用户上传的皮肤图片和文字描述，输出一个 JSON 对象。",
                "不要输出 Markdown，不要输出额外解释，也不要给出最终医学确诊。",
                "你必须返回 JSON，并包含这些字段：prompt_version、image_observation、possible_conditions、risk_level、care_advice、hospital_advice、high_risk_alert、disclaimer。",
                "possible_conditions 和 care_advice 必须返回数组。",
                "risk_level 只能是 LOW、MEDIUM、HIGH 之一。",
                f"症状描述：{complaint or '未填写'}",
                f"健康档案摘要：{health_summary or '未填写'}",
            ]
        )

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    *[self._build_image_part(url) for url in image_urls],
                ],
            }
        ]

        response = httpx.post(
            f"{settings.qwen_base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.qwen_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.qwen_visual_model,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 1200,
                "response_format": {"type": "json_object"},
                "enable_thinking": False,
            },
            timeout=httpx.Timeout(45.0, connect=10.0),
        )
        response.raise_for_status()
        payload = response.json()

        content = payload["choices"][0]["message"]["content"]
        if isinstance(content, list):
            content = "".join(item.get("text", "") for item in content if isinstance(item, dict))

        data = self._load_json(content)
        possible_conditions = self._normalize_text_lines(data.get("possible_conditions"))
        care_advice = self._normalize_text_lines(data.get("care_advice"))
        risk_level = self._normalize_risk(data.get("risk_level"))

        return AIResult(
            model_name=settings.qwen_visual_model,
            prompt_version=str(data.get("prompt_version") or "consultation-v1"),
            image_observation=str(data.get("image_observation") or "未返回图像观察结果。"),
            possible_conditions=possible_conditions or "信息不足，暂未返回明确方向。",
            risk_level=risk_level,
            care_advice=care_advice or "请结合面部变化持续观察，如有加重及时就医。",
            hospital_advice=str(data.get("hospital_advice") or "如症状持续加重，请尽快线下就医。"),
            high_risk_alert=str(data.get("high_risk_alert") or DEFAULT_HIGH_RISK_ALERT),
            disclaimer=str(data.get("disclaimer") or DEFAULT_DISCLAIMER),
            raw_response=json.dumps(payload, ensure_ascii=False),
        )

    def _build_image_part(self, image_url: str) -> dict:
        if image_url.startswith("data:image/"):
            return {"type": "image_url", "image_url": {"url": image_url}}

        local_path = self._resolve_local_upload_path(image_url)
        if local_path:
            mime_type = mimetypes.guess_type(local_path.name)[0] or "image/jpeg"
            encoded = base64.b64encode(local_path.read_bytes()).decode("utf-8")
            return {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded}"}}

        return {"type": "image_url", "image_url": {"url": image_url}}

    def _resolve_local_upload_path(self, image_url: str) -> Path | None:
        parsed = urlparse(image_url)
        path = parsed.path if parsed.scheme else image_url
        if not path.startswith("/uploads/"):
            return None

        relative = unquote(path.removeprefix("/uploads/"))
        safe_parts = [part for part in relative.split("/") if part and part not in {".", ".."}]
        if not safe_parts:
            return None

        candidate = settings.upload_path.joinpath(*safe_parts).resolve()
        upload_root = settings.upload_path.resolve()
        if upload_root not in candidate.parents and candidate != upload_root:
            return None
        if not candidate.is_file():
            return None
        return candidate

    @staticmethod
    def _load_json(content: str) -> dict:
        text = content.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise
            return json.loads(text[start : end + 1])

    @staticmethod
    def _normalize_text_lines(value: object) -> str:
        if isinstance(value, list):
            lines = [str(item).strip() for item in value if str(item).strip()]
            return "\n".join(lines)
        if isinstance(value, str):
            return value.strip()
        return ""

    @staticmethod
    def _normalize_risk(value: object) -> str:
        if isinstance(value, str):
            normalized = value.strip().upper()
            if normalized in {"LOW", "MEDIUM", "HIGH"}:
                return normalized
        return "MEDIUM"


analyzer = VisualAnalyzer()
