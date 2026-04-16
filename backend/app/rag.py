from __future__ import annotations

import json
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.model import KnowledgeChunkMetadata, KnowledgeDocument


class RAGEngine:
    def tokenize(self, question: str) -> list[str]:
        words = re.findall(r"[\\u4e00-\\u9fff]{1,4}|[A-Za-z0-9_]+", question)
        extras: list[str] = []
        for word in words:
            if len(word) > 2:
                extras.extend([word[:2], word[-2:]])
        return list(dict.fromkeys(words + extras))

    def retrieve(self, db: Session, question: str) -> list[dict]:
        rows = db.execute(
            select(KnowledgeChunkMetadata, KnowledgeDocument)
            .join(KnowledgeDocument, KnowledgeChunkMetadata.document_id == KnowledgeDocument.id)
            .where(KnowledgeChunkMetadata.enabled_flag == 1, KnowledgeDocument.enabled_flag == 1)
        ).all()
        tokens = self.tokenize(question)
        scored: list[dict] = []
        for chunk, document in rows:
            haystack = f"{document.doc_title} {document.category or ''} {document.tag_list or ''} {chunk.chunk_text} {chunk.keywords or ''}"
            score = sum(2 for token in tokens if token and token in haystack)
            if score:
                scored.append(
                    {
                        "document_id": document.id,
                        "document_title": document.doc_title,
                        "chunk_id": chunk.id,
                        "snippet": chunk.chunk_text[:110] + ("..." if len(chunk.chunk_text) > 110 else ""),
                        "score": score,
                    }
                )
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:3] if scored else []

    def answer(self, db: Session, question: str) -> tuple[str, list[dict], str]:
        refs = self.retrieve(db, question)
        if "痤疮" in question or "粉刺" in question or "爆痘" in question:
            intro = "痤疮通常与皮脂分泌旺盛、作息紊乱、毛囊角化和不当挤压有关。"
        elif "过敏" in question or "湿疹" in question or "瘙痒" in question:
            intro = "湿疹和过敏性皮炎往往与皮肤屏障受损、接触刺激物或过敏原有关。"
        elif "脚气" in question or "真菌" in question or "体癣" in question:
            intro = "真菌感染常与潮湿闷热环境和共用毛巾鞋袜有关，重点是保持干燥和规范用药。"
        else:
            intro = "针对你的问题，建议优先判断诱因、持续时长和是否伴随疼痛、渗液或范围扩大。"
        evidence = " ".join(item["snippet"] for item in refs)[:130]
        answer = (
            f"{intro} 结合检索到的知识条目，建议先从温和清洁、规律作息、减少刺激和记录病情变化做起。"
            f" 参考摘要：{evidence or '当前命中内容较少，建议继续补充更具体症状。'} "
            "医疗辅助免责声明：本回答基于知识检索增强生成，仅供健康参考，不作为医学诊断结论。"
        )
        risk_hint = "若伴疼痛、渗液、发热、范围扩大或反复不缓解，应尽快前往皮肤科线下面诊。"
        return answer, refs, risk_hint

    @staticmethod
    def dump_refs(refs: list[dict]) -> str:
        return json.dumps(refs, ensure_ascii=False)


rag_engine = RAGEngine()
