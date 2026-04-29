from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select


ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.chat_graph import TextChatService
from app.chat_store import ensure_chat_tables
from app.db import SessionLocal
from app.main import app
from app.model import ChatSession, ToolCallLog, User


DEFAULT_USERNAME = os.getenv("TEXT_CHAT_SMOKE_USER", "user01")
DEFAULT_PASSWORD = os.getenv("TEXT_CHAT_SMOKE_PASSWORD", "12345678")


def unwrap(response):
    if response.status_code != 200:
        raise AssertionError(f"HTTP {response.status_code}: {response.text}")
    payload = response.json()
    if payload.get("code") != 0:
        raise AssertionError(json.dumps(payload, ensure_ascii=False, indent=2))
    return payload["data"]


def assert_contains_any(text: str, tokens: list[str], message: str) -> None:
    if not any(token in text for token in tokens):
        raise AssertionError(f"{message}，实际回答：{text}")


def login_or_register(client: TestClient) -> tuple[str, str]:
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": DEFAULT_USERNAME, "password": DEFAULT_PASSWORD},
    )
    if login_response.status_code == 200 and login_response.json().get("code") == 0:
        token = login_response.json()["data"]["access_token"]
        return token, DEFAULT_USERNAME

    temp_username = f"smoke_{uuid.uuid4().hex[:8]}"
    temp_password = "Smoke12345"
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "username": temp_username,
            "password": temp_password,
            "confirm_password": temp_password,
            "role_type": "USER",
        },
    )
    unwrap(register_response)

    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": temp_username, "password": temp_password},
    )
    token = unwrap(login_response)["access_token"]
    return token, temp_username


def run_api_smoke(client: TestClient, headers: dict[str, str]) -> list[dict[str, object]]:
    created = unwrap(
        client.post(
            "/api/v1/chat/sessions",
            json={"title": f"LangGraph 冒烟测试 {datetime.now().strftime('%H%M%S')}"},
            headers=headers,
        )
    )
    session_id = created["session_id"]

    cases = [
        {
            "name": "direct_answer",
            "message": "湿疹是什么？",
            "intent": "DIRECT_ANSWER",
            "used_tool": False,
            "answer_tokens": ["湿疹", "炎症", "皮肤"],
        },
        {
            "name": "history_followup",
            "message": "那它和过敏有什么关系？",
            "intent": "DIRECT_ANSWER",
            "used_tool": False,
            "answer_tokens": ["湿疹", "过敏", "屏障"],
        },
        {
            "name": "web_search",
            "message": "最近有没有湿疹治疗的新指南？",
            "intent": "WEB_SEARCH",
            "used_tool": True,
            "answer_tokens": ["指南", "公开", "医生"],
        },
        {
            "name": "system_help",
            "message": "我怎么上传皮肤图片？",
            "intent": "SYSTEM_HELP",
            "used_tool": False,
            "answer_tokens": ["图文问诊", "上传", "页面"],
        },
        {
            "name": "medical_risk",
            "message": "皮肤破溃并且发热怎么办？",
            "intent": "MEDICAL_RISK",
            "used_tool": False,
            "answer_tokens": ["就医", "线下", "及时"],
        },
    ]

    results: list[dict[str, object]] = []
    for case in cases:
        response = unwrap(
            client.post(
                f"/api/v1/chat/sessions/{session_id}/messages",
                json={"message": case["message"]},
                headers=headers,
            )
        )
        if response["intent"] != case["intent"]:
            raise AssertionError(f"{case['name']} intent 异常: {response['intent']} != {case['intent']}")
        if bool(response["used_tool"]) != bool(case["used_tool"]):
            raise AssertionError(f"{case['name']} used_tool 异常: {response['used_tool']} != {case['used_tool']}")
        if case["used_tool"] and not response.get("sources"):
            raise AssertionError(f"{case['name']} 未返回来源")
        assert_contains_any(response["answer"], case["answer_tokens"], f"{case['name']} 回答缺少预期信息")
        results.append(
            {
                "case": case["name"],
                "intent": response["intent"],
                "used_tool": bool(response["used_tool"]),
                "sources": len(response.get("sources", [])),
                "answer_preview": response["answer"][:80],
            }
        )

    history = unwrap(client.get(f"/api/v1/chat/sessions/{session_id}/messages", headers=headers))
    if len(history["messages"]) != 10:
        raise AssertionError(f"历史消息条数异常: {len(history['messages'])} != 10")

    return results


class RouterOnlyLLM:
    def chat(self, messages: list[dict], *, json_mode: bool = False) -> str:
        if json_mode:
            return json.dumps(
                {
                    "intent": "WEB_SEARCH",
                    "need_tavily": True,
                    "reason": "smoke fallback",
                    "search_query": "最近有没有湿疹治疗的新指南？",
                },
                ensure_ascii=False,
            )
        return "unused"


class FailingTavily:
    def search(self, query: str):
        raise RuntimeError("simulated tavily outage")


def run_tavily_fallback_smoke(username: str) -> dict[str, object]:
    with SessionLocal() as db:
        ensure_chat_tables(db)
        user = db.scalar(select(User).where(User.username == username, User.is_deleted == 0))
        if not user:
            raise AssertionError(f"找不到测试用户：{username}")

        now = datetime.now(UTC).replace(tzinfo=None)
        session = ChatSession(
            user_id=user.id,
            title=f"Tavily Fallback {uuid.uuid4().hex[:6]}",
            created_at=now,
            updated_at=now,
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        service = TextChatService(
            db,
            user.id,
            llm_client=RouterOnlyLLM(),
            tavily_client=FailingTavily(),
        )
        state = service.run(session, "最近有没有湿疹治疗的新指南？")
        log = db.scalar(select(ToolCallLog).where(ToolCallLog.message_id == state["saved_message_id"]))

        if not log:
            raise AssertionError("Tavily 失败兜底未写入工具日志")
        if log.success != 0:
            raise AssertionError(f"Tavily 失败兜底日志 success 异常: {log.success}")
        if not log.error_message or "simulated tavily outage" not in log.error_message:
            raise AssertionError(f"Tavily 失败兜底日志错误信息异常: {log.error_message}")
        assert_contains_any(
            state["final_answer"],
            ["没能完成联网检索", "无法帮你核实最新信息", "稍后重试"],
            "Tavily 失败兜底回答不符合预期",
        )

        return {
            "case": "tavily_fallback",
            "intent": state.get("intent"),
            "used_tool": bool(state.get("used_tool")),
            "logged_error": log.error_message,
            "answer_preview": state["final_answer"][:80],
        }


def main() -> int:
    client = TestClient(app)
    token, username = login_or_register(client)
    headers = {"Authorization": f"Bearer {token}"}

    api_results = run_api_smoke(client, headers)
    fallback_result = run_tavily_fallback_smoke(username)

    print("TEXT_CHAT_SMOKE_OK")
    print(json.dumps({"api": api_results, "fallback": fallback_result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
