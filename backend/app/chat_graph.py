from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, TypedDict

import httpx
try:
    from langgraph.graph import END, START, StateGraph

    HAS_LANGGRAPH = True
except Exception:
    END = "__end__"
    START = "__start__"
    StateGraph = None
    HAS_LANGGRAPH = False
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.chat_store import build_session_title, touch_session
from app.config import get_settings
from app.model import ChatMessage, ChatSession, ToolCallLog


settings = get_settings()

DEFAULT_SESSION_TITLE = "新的对话"
DISCLAIMER = "温馨提示：以上内容仅供健康参考，不能替代医生面诊和正式诊断。"
SYSTEM_HELP_CONTEXT = """
你正在回答“肤联智诊”系统功能问题。当前已知功能如下：
1. 用户可以在图文问诊页面上传皮肤图片并提交问诊。
2. 文本知识问答页面主要处理文字提问，不负责上传图片。
3. 图文问诊会结合图片、症状描述和医生协同给出建议。
4. 如需查看历史记录，可在记录/历史相关页面查看。
5. 如遇严重不适，应优先建议及时线下就医，而不是停留在系统内等待。
""".strip()

ROUTER_PROMPT = """
你是 肤联智诊 的问答路由器。请判断用户问题应该如何处理。

你只能输出 JSON，不要输出 Markdown，不要解释。

可选 intent：
- DIRECT_ANSWER：普通皮肤健康科普、护理建议、常见问答
- WEB_SEARCH：最新信息、实时政策、医院、药品、指南更新
- CLARIFY：问题过于模糊，需要追问
- SYSTEM_HELP：系统功能使用问题
- MEDICAL_RISK：疑似高风险症状，需要建议及时就医

输出格式：
{
  "intent": "DIRECT_ANSWER | WEB_SEARCH | CLARIFY | SYSTEM_HELP | MEDICAL_RISK",
  "need_tavily": true 或 false,
  "reason": "简短原因",
  "search_query": "如果需要搜索，给出中文搜索词；否则为空字符串"
}

规则：
1. 不要所有问题都调用 Tavily。
2. 普通知识问答不调用 Tavily。
3. 涉及“最近、最新、现在、附近、政策、药品通报、指南更新”等实时信息时，调用 Tavily。
4. 涉及严重症状，如发热、破溃、迅速扩散、剧烈疼痛，应标记为 MEDICAL_RISK。
5. 涉及上传图片、怎么看历史、怎么发问诊等系统使用问题，应标记为 SYSTEM_HELP。
6. 用户问题太短或缺少必要信息时，标记为 CLARIFY。
""".strip()

DIRECT_ANSWER_PROMPT = """
你是 肤联智诊 的皮肤健康问答助手。

请根据用户问题和历史对话，用中文回答。

要求：
1. 回答要清楚、克制、易懂。
2. 不要给出最终医学诊断。
3. 可以提供常见原因、护理建议、就医建议。
4. 如果 intent 为 MEDICAL_RISK，优先给出风险提醒并建议尽快线下就医。
5. 如果 intent 为 SYSTEM_HELP，只根据系统功能说明回答，不要编造不存在的功能。
6. 如果 intent 为 CLARIFY，请只追问最关键的 1 到 2 个补充信息点。
7. 不要编造药品、医院、指南或最新政策。
8. 结尾加一句简短免责声明。
""".strip()

TOOL_ANSWER_PROMPT = """
你是 肤联智诊 的皮肤健康问答助手。

下面是 Tavily 搜索得到的公开信息摘要。请结合用户问题和搜索结果，用中文生成最终回答。

要求：
1. 不要逐字复制搜索结果。
2. 只总结和用户问题相关的信息。
3. 如果搜索结果不足以支持结论，要明确说明。
4. 不要给出最终医学诊断。
5. 涉及药物、治疗、指南时，要提醒用户咨询医生。
6. 回答末尾加免责声明。
7. 返回内容要适合前端直接展示。
""".strip()

SEARCH_KEYWORDS = {
    "最近",
    "最新",
    "现在",
    "实时",
    "附近",
    "政策",
    "新闻",
    "指南",
    "药品",
    "通报",
    "价格",
    "医院",
    "发布",
    "更新",
}
MEDICAL_RISK_KEYWORDS = {
    "发热",
    "破溃",
    "剧烈疼痛",
    "迅速扩散",
    "流脓",
    "呼吸困难",
    "严重过敏",
}
SYSTEM_HELP_KEYWORDS = {
    "上传图片",
    "上传皮肤图片",
    "怎么上传",
    "怎么用",
    "历史记录",
    "问诊页",
    "系统功能",
}


class HistoryItem(TypedDict):
    role: str
    content: str


class SourceItem(TypedDict):
    title: str
    url: str
    summary: str


class ChatState(TypedDict, total=False):
    session_id: int
    user_id: int
    user_message: str
    history: list[HistoryItem]
    intent: str
    need_tavily: bool
    route_reason: str
    search_query: str
    tavily_results: list[SourceItem]
    sources: list[SourceItem]
    final_answer: str
    model_name: str
    used_tool: bool
    tool_name: str | None
    tool_query: str
    tool_error: str | None
    tool_latency_ms: int | None
    saved_message_id: int
    created_at: str


@dataclass
class RouterDecision:
    intent: str
    need_tavily: bool
    reason: str
    search_query: str


class QwenTextClient:
    def __init__(self) -> None:
        self.api_key = settings.qwen_api_key
        self.base_url = settings.qwen_base_url
        self.model = settings.text_qa_model or settings.qwen_text_model

    def chat(self, messages: list[dict], *, json_mode: bool = False) -> str:
        if not self.api_key or not self.base_url:
            raise RuntimeError("文本问答模型未配置")

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": settings.chat_temperature,
            "max_tokens": settings.chat_max_tokens,
            "enable_thinking": False,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        response = httpx.post(
            f"{self.base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=httpx.Timeout(float(settings.chat_timeout_seconds), connect=10.0),
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        if isinstance(content, list):
            return "".join(str(item.get("text", "")) for item in content if isinstance(item, dict)).strip()
        return str(content).strip()


class TavilySearchClient:
    def __init__(self) -> None:
        self.api_key = settings.tavily_api_key

    def search(self, query: str) -> list[SourceItem]:
        if not settings.tavily_enabled or not self.api_key:
            raise RuntimeError("Tavily 未启用")

        response = httpx.post(
            "https://api.tavily.com/search",
            json={
                "api_key": self.api_key,
                "query": query,
                "topic": "general",
                "search_depth": "basic",
                "max_results": 3,
                "include_answer": False,
                "include_images": False,
                "include_raw_content": False,
            },
            timeout=httpx.Timeout(float(settings.chat_timeout_seconds), connect=10.0),
        )
        response.raise_for_status()
        data = response.json()
        items: list[SourceItem] = []
        for row in data.get("results", [])[:3]:
            items.append(
                {
                    "title": str(row.get("title") or "未命名来源").strip(),
                    "url": str(row.get("url") or "").strip(),
                    "summary": str(row.get("content") or row.get("snippet") or "").strip(),
                }
            )
        return items


class TextChatService:
    def __init__(
        self,
        db: Session,
        user_id: int,
        *,
        llm_client: QwenTextClient | None = None,
        tavily_client: TavilySearchClient | None = None,
    ) -> None:
        self.db = db
        self.user_id = user_id
        self.llm_client = llm_client or QwenTextClient()
        self.tavily_client = tavily_client or TavilySearchClient()
        self.model_name = settings.text_qa_model or settings.qwen_text_model

    def run(self, session: ChatSession, user_message: str) -> ChatState:
        initial_state: ChatState = {
            "session_id": session.id,
            "user_id": self.user_id,
            "user_message": user_message.strip(),
            "model_name": self.model_name,
            "used_tool": False,
            "tool_name": None,
            "sources": [],
            "tavily_results": [],
            "tool_error": None,
            "tool_latency_ms": None,
            "tool_query": "",
        }
        if HAS_LANGGRAPH and StateGraph is not None:
            graph = self._build_graph()
            return graph.invoke(initial_state)
        return self._run_without_langgraph(initial_state)

    def _build_graph(self):
        workflow = StateGraph(ChatState)
        workflow.add_node("load_history", self.load_history_node)
        workflow.add_node("router", self.router_node)
        workflow.add_node("direct_answer", self.direct_answer_node)
        workflow.add_node("tavily_search", self.tavily_search_node)
        workflow.add_node("tool_answer", self.tool_answer_node)
        workflow.add_node("save_message", self.save_message_node)

        workflow.add_edge(START, "load_history")
        workflow.add_edge("load_history", "router")
        workflow.add_conditional_edges(
            "router",
            self.route_after_router,
            {
                "direct_answer": "direct_answer",
                "web_search": "tavily_search",
            },
        )
        workflow.add_edge("direct_answer", "save_message")
        workflow.add_edge("tavily_search", "tool_answer")
        workflow.add_edge("tool_answer", "save_message")
        workflow.add_edge("save_message", END)
        return workflow.compile()

    def _run_without_langgraph(self, initial_state: ChatState) -> ChatState:
        state: ChatState = dict(initial_state)
        state.update(self.load_history_node(state))
        state.update(self.router_node(state))
        next_step = self.route_after_router(state)
        if next_step == "web_search":
            state.update(self.tavily_search_node(state))
            state.update(self.tool_answer_node(state))
        else:
            state.update(self.direct_answer_node(state))
        state.update(self.save_message_node(state))
        return state

    def load_history_node(self, state: ChatState) -> ChatState:
        rows = (
            self.db.execute(
                select(ChatMessage)
                .where(ChatMessage.session_id == state["session_id"])
                .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
            )
            .scalars()
            .all()
        )
        limited = rows[-settings.chat_history_limit :] if settings.chat_history_limit > 0 else rows
        history: list[HistoryItem] = [{"role": row.role, "content": row.content} for row in limited]
        return {"history": history}

    def router_node(self, state: ChatState) -> ChatState:
        history_text = self._render_history(state.get("history", []))
        prompt = (
            f"历史对话：\n{history_text or '无'}\n\n"
            f"当前问题：{state['user_message']}\n"
            "请输出 JSON。"
        )
        try:
            content = self.llm_client.chat(
                [
                    {"role": "system", "content": ROUTER_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                json_mode=True,
            )
            decision = self._parse_router_decision(content)
        except Exception:
            decision = self._heuristic_route(state["user_message"])

        return {
            "intent": decision.intent,
            "need_tavily": decision.need_tavily,
            "route_reason": decision.reason,
            "search_query": decision.search_query,
        }

    def route_after_router(self, state: ChatState) -> Literal["direct_answer", "web_search"]:
        if state.get("intent") == "WEB_SEARCH" and state.get("need_tavily"):
            return "web_search"
        return "direct_answer"

    def direct_answer_node(self, state: ChatState) -> ChatState:
        history_text = self._render_history(state.get("history", []))
        prompt = (
            f"当前意图：{state.get('intent') or 'DIRECT_ANSWER'}\n"
            f"{SYSTEM_HELP_CONTEXT}\n\n"
            f"历史对话：\n{history_text or '无'}\n\n"
            f"用户问题：{state['user_message']}\n"
        )
        try:
            answer = self.llm_client.chat(
                [
                    {"role": "system", "content": DIRECT_ANSWER_PROMPT},
                    {"role": "user", "content": prompt},
                ]
            )
        except Exception:
            answer = f"我暂时无法连接文本问答模型，请稍后重试。{DISCLAIMER}"

        return {
            "final_answer": self._ensure_disclaimer(answer),
            "used_tool": False,
            "tool_name": None,
            "sources": [],
        }

    def tavily_search_node(self, state: ChatState) -> ChatState:
        query = state.get("search_query") or state["user_message"]
        started = time.perf_counter()
        try:
            results = self.tavily_client.search(query)
            latency_ms = int((time.perf_counter() - started) * 1000)
            return {
                "used_tool": True,
                "tool_name": "tavily",
                "tool_query": query,
                "tool_latency_ms": latency_ms,
                "tavily_results": results,
                "sources": results,
                "tool_error": None,
            }
        except Exception as exc:
            latency_ms = int((time.perf_counter() - started) * 1000)
            return {
                "used_tool": False,
                "tool_name": "tavily",
                "tool_query": query,
                "tool_latency_ms": latency_ms,
                "tavily_results": [],
                "sources": [],
                "tool_error": str(exc),
            }

    def tool_answer_node(self, state: ChatState) -> ChatState:
        if state.get("tool_error"):
            answer = (
                "我本次没能完成联网检索，因此无法帮你核实最新信息。"
                "建议稍后重试，或直接查看权威医院、指南或官方公告。"
            )
            return {
                "final_answer": self._ensure_disclaimer(answer),
                "used_tool": False,
                "sources": [],
            }

        sources = state.get("sources", [])
        if not sources:
            answer = "我没有检索到足够可靠的公开信息来支持明确结论，建议稍后再试或换一个更具体的问题。"
            return {
                "final_answer": self._ensure_disclaimer(answer),
                "used_tool": False,
                "sources": [],
            }

        history_text = self._render_history(state.get("history", []))
        source_text = "\n".join(
            [
                f"{index}. 标题：{item['title']}\n链接：{item['url']}\n摘要：{item['summary'] or '无'}"
                for index, item in enumerate(sources, start=1)
            ]
        )
        prompt = (
            f"历史对话：\n{history_text or '无'}\n\n"
            f"用户问题：{state['user_message']}\n\n"
            f"搜索结果：\n{source_text}"
        )
        try:
            answer = self.llm_client.chat(
                [
                    {"role": "system", "content": TOOL_ANSWER_PROMPT},
                    {"role": "user", "content": prompt},
                ]
            )
        except Exception:
            answer = "我拿到了部分公开来源，但本次整理回答失败。你可以先查看下方来源链接，或稍后重新发起提问。"

        return {
            "final_answer": self._ensure_disclaimer(answer),
            "used_tool": True,
            "tool_name": "tavily",
            "sources": sources,
        }

    def save_message_node(self, state: ChatState) -> ChatState:
        now = datetime.utcnow()
        session = self.db.scalar(select(ChatSession).where(ChatSession.id == state["session_id"], ChatSession.user_id == self.user_id))
        if not session:
            raise RuntimeError("会话不存在")

        if not session.title or session.title == DEFAULT_SESSION_TITLE:
            session.title = build_session_title(state["user_message"], fallback=DEFAULT_SESSION_TITLE)
        touch_session(session, now)

        user_row = ChatMessage(
            session_id=session.id,
            user_id=self.user_id,
            role="user",
            content=state["user_message"],
            intent=state.get("intent"),
            used_tool=0,
            tool_name=None,
            sources_json=None,
            model_name=None,
            created_at=now,
        )
        self.db.add(user_row)
        self.db.flush()

        assistant_row = ChatMessage(
            session_id=session.id,
            user_id=self.user_id,
            role="assistant",
            content=state["final_answer"],
            intent=state.get("intent"),
            used_tool=1 if state.get("used_tool") else 0,
            tool_name=state.get("tool_name") if state.get("used_tool") else None,
            sources_json=json.dumps(state.get("sources", []), ensure_ascii=False),
            model_name=state.get("model_name") or self.model_name,
            created_at=now,
        )
        self.db.add(assistant_row)
        self.db.flush()

        if state.get("tool_name"):
            self.db.add(
                ToolCallLog(
                    session_id=session.id,
                    message_id=assistant_row.id,
                    tool_name=state["tool_name"],
                    query=state.get("tool_query") or state["user_message"],
                    result_json=json.dumps(state.get("sources", []), ensure_ascii=False) if state.get("sources") else None,
                    latency_ms=state.get("tool_latency_ms"),
                    success=0 if state.get("tool_error") else 1,
                    error_message=state.get("tool_error"),
                    created_at=now,
                )
            )

        self.db.commit()
        return {
            "saved_message_id": assistant_row.id,
            "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        }

    @staticmethod
    def _render_history(history: list[HistoryItem]) -> str:
        return "\n".join(f"{item['role']}: {item['content']}" for item in history[-settings.chat_history_limit :])

    @staticmethod
    def _parse_router_decision(content: str) -> RouterDecision:
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise
            data = json.loads(content[start : end + 1])

        intent = str(data.get("intent") or "DIRECT_ANSWER").strip().upper()
        if intent not in {"DIRECT_ANSWER", "WEB_SEARCH", "CLARIFY", "SYSTEM_HELP", "MEDICAL_RISK"}:
            intent = "DIRECT_ANSWER"
        need_tavily = bool(data.get("need_tavily")) and intent == "WEB_SEARCH"
        search_query = str(data.get("search_query") or "").strip()
        return RouterDecision(
            intent=intent,
            need_tavily=need_tavily,
            reason=str(data.get("reason") or "").strip(),
            search_query=search_query,
        )

    @staticmethod
    def _heuristic_route(message: str) -> RouterDecision:
        lowered = message.lower()
        if any(keyword in message for keyword in MEDICAL_RISK_KEYWORDS):
            return RouterDecision("MEDICAL_RISK", False, "命中医疗风险关键词", "")
        if any(keyword in message for keyword in SYSTEM_HELP_KEYWORDS):
            return RouterDecision("SYSTEM_HELP", False, "命中系统帮助关键词", "")
        if any(keyword in message for keyword in SEARCH_KEYWORDS):
            return RouterDecision("WEB_SEARCH", True, "命中实时搜索关键词", message.strip())
        if len(message.strip()) <= 2:
            return RouterDecision("CLARIFY", False, "问题过短，需要补充", "")
        if "?" not in lowered and "？" not in message and len(message.strip()) < 6:
            return RouterDecision("CLARIFY", False, "信息不足", "")
        return RouterDecision("DIRECT_ANSWER", False, "默认直接回答", "")

    @staticmethod
    def _ensure_disclaimer(answer: str) -> str:
        text = answer.strip()
        if DISCLAIMER in text:
            return text
        if text.endswith(("。", "！", "？")):
            return f"{text}\n\n{DISCLAIMER}"
        return f"{text}。\n\n{DISCLAIMER}"
