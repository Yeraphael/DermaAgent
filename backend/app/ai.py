from __future__ import annotations

import json
from dataclasses import dataclass

import httpx

from app.config import get_settings


settings = get_settings()


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
            except Exception:
                pass
        return self._mock_call(complaint, image_urls, health_summary)

    def _mock_call(self, complaint: str, image_urls: list[str], health_summary: str) -> AIResult:
        text = f"{complaint} {health_summary}"
        risk = "LOW"
        image_observation = "上传图片中可见局灶性表浅皮损，炎症程度相对有限。"
        possible_conditions = "轻度痤疮、局部刺激反应、毛囊周围炎症等方向"
        care_advice = "建议保持温和清洁，避免挤压、刷酸叠加和频繁触碰患处。"
        hospital_advice = "若 3~5 天内持续加重或反复发作，可预约皮肤科进一步面诊。"
        high_risk_alert = "高风险就医提醒：若红肿迅速扩大、伴发热或流脓，请尽快线下就医。"
        if any(keyword in text for keyword in ["痘", "粉刺", "丘疹", "闭口"]):
            image_observation = "图文信息提示丘疹、粉刺样改变较为突出，炎症程度偏轻至中等。"
            possible_conditions = "痤疮倾向、毛囊炎、油脂分泌相关皮损"
            care_advice = "优先减少高糖高油饮食和熬夜，使用温和洁面，暂停自行挤压与强刺激护肤。"
        elif any(keyword in text for keyword in ["过敏", "红斑", "瘙痒", "刺痛", "泛红"]):
            risk = "MEDIUM"
            image_observation = "更像是屏障受损后的炎症性皮损，常伴红斑、瘙痒与刺激感。"
            possible_conditions = "接触性皮炎、过敏性皮炎、湿疹样改变"
            care_advice = "建议暂停近期新增护肤和彩妆，冷敷减轻不适，并加强无香精保湿。"
            hospital_advice = "若红斑持续扩大、夜间瘙痒明显或影响睡眠，建议尽快线下面诊。"
        elif any(keyword in text for keyword in ["渗液", "化脓", "发热", "水疱", "破溃", "大面积"]):
            risk = "HIGH"
            image_observation = "图文信息提示皮损活动度较高，可能伴渗出、破溃或继发感染风险。"
            possible_conditions = "中重度湿疹急性发作、继发感染、带状分布皮损或其他高风险炎症"
            care_advice = "保持患处清洁和干燥，避免自行挑破水疱或重复使用刺激性药物。"
            hospital_advice = "建议尽快前往皮肤科或综合医院门诊，由医生面对面评估。"
            high_risk_alert = "高风险就医提醒：若伴发热、明显疼痛、流脓或范围迅速扩大，请立即线下就医。"
        disclaimer = "医疗辅助免责声明：本结果仅供健康参考，不能替代医生面诊与医学诊断。"
        raw_response = json.dumps({"complaint": complaint, "images": len(image_urls), "health_summary": health_summary}, ensure_ascii=False)
        return AIResult(
            model_name="mock-qwen-vl",
            prompt_version="v1.0.0",
            image_observation=image_observation,
            possible_conditions=possible_conditions,
            risk_level=risk,
            care_advice=care_advice,
            hospital_advice=hospital_advice,
            high_risk_alert=high_risk_alert,
            disclaimer=disclaimer,
            raw_response=raw_response,
        )

    def _real_call(self, complaint: str, image_urls: list[str], health_summary: str) -> AIResult:
        messages = [
            {"role": "system", "content": "你是皮肤健康辅助分析助手，只输出结构化 JSON，不输出最终诊断结论。"},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"症状描述：{complaint}\\n健康摘要：{health_summary}"},
                    *[{"type": "image_url", "image_url": {"url": url}} for url in image_urls],
                ],
            },
        ]
        response = httpx.post(
            f"{settings.qwen_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.qwen_api_key}", "Content-Type": "application/json"},
            json={"model": settings.qwen_visual_model, "messages": messages, "temperature": 0.2},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        content = payload["choices"][0]["message"]["content"]
        if isinstance(content, list):
            content = "".join(item.get("text", "") for item in content if isinstance(item, dict))
        data = json.loads(content)
        return AIResult(
            model_name=settings.qwen_visual_model,
            prompt_version=data.get("prompt_version", "real-v1"),
            image_observation=data.get("image_observation", ""),
            possible_conditions=data.get("possible_conditions", ""),
            risk_level=data.get("risk_level", "MEDIUM"),
            care_advice=data.get("care_advice", ""),
            hospital_advice=data.get("hospital_advice", ""),
            high_risk_alert=data.get("high_risk_alert", "高风险就医提醒：如出现明显加重，请尽快线下就医。"),
            disclaimer=data.get("disclaimer", "医疗辅助免责声明：本结果仅供健康参考。"),
            raw_response=json.dumps(payload, ensure_ascii=False),
        )


analyzer = VisualAnalyzer()
