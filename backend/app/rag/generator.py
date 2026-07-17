"""
RAG 生成器 — Prompt 模板 + LLM 生成 + 置信度决策
"""
from app.llm.base import BaseLLMProvider, ChatMessage
from app.llm.factory import get_llm_provider
from app.core.config import settings

RAG_SYSTEM_PROMPT = """你是SmartCS电商平台的智能客服助手。
请基于以下参考资料回答用户的问题。
规则：
1. 如果参考资料足以回答，请简洁专业地回复
2. 如果参考资料部分相关但不完整，基于已有信息回复并说明这是你目前掌握的信息
3. 如果参考资料完全无法回答用户问题，请明确说"抱歉，我暂时无法回答这个问题，正在为您转接人工客服"
4. 回复要友好、专业，控制在200字以内
5. 如果用户询问尺码，优先参考尺码表，结合用户提供的身高体重推荐

参考资料：
{context}"""


class RAGGenerator:
    """
    RAG 回复生成器 — 负责 Prompt 构建、LLM 调用、置信度决策。
    """

    def __init__(self):
        self.llm: BaseLLMProvider = get_llm_provider()

    def _build_context(self, top_chunks: list[dict]) -> str:
        """从检索结果构建上下文文本"""
        parts = []
        for i, chunk in enumerate(top_chunks, 1):
            title = chunk.get("title", "无标题")
            content = chunk.get("content", "")
            source = chunk.get("source_type", "未知")
            parts.append(f"[{i}] ({source}) {title}\n{content}")
        return "\n\n".join(parts)

    def _build_messages(self, query: str, context: str, chat_history: list[dict] | None = None) -> list[ChatMessage]:
        """构建 LLM 消息列表"""
        messages = [
            ChatMessage(role="system", content=RAG_SYSTEM_PROMPT.format(context=context)),
        ]
        # 添加历史消息（最近 5 轮）
        if chat_history:
            for h in chat_history[-10:]:
                messages.append(ChatMessage(role=h.get("role", "user"), content=h.get("content", "")))
        messages.append(ChatMessage(role="user", content=query))
        return messages

    async def generate(
        self,
        query: str,
        top_chunks: list[dict],
        chat_history: list[dict] | None = None,
    ) -> dict:
        """
        生成回复 + 置信度评估。

        Returns:
            {
                "answer": str,
                "confidence": float (0-1),
                "sources": list[dict],
                "decision": "auto_reply" | "suggest" | "handoff"
            }
        """
        if not top_chunks or top_chunks[0].get("score", 0) < settings.RAG_CONFIDENCE_MEDIUM:
            return {
                "answer": "抱歉，我暂时无法回答这个问题，正在为您转接人工客服。",
                "confidence": 0.0,
                "sources": [],
                "decision": "handoff",
            }

        context = self._build_context(top_chunks[: settings.RAG_RERANK_TOP_K])
        messages = self._build_messages(query, context, chat_history)

        max_score = top_chunks[0].get("score", 0)

        if max_score >= settings.RAG_CONFIDENCE_HIGH:
            # 高置信度：自动回复
            resp = await self.llm.chat(messages, temperature=0.3, max_tokens=512)
            return {
                "answer": resp.content,
                "confidence": max_score,
                "sources": [{"title": c.get("title"), "content": c.get("content")[:200], "score": c.get("score")} for c in top_chunks[:3]],
                "decision": "auto_reply",
            }
        else:
            # 中等置信度：生成建议给人工客服
            resp = await self.llm.chat(messages, temperature=0.3, max_tokens=512)
            return {
                "answer": resp.content,
                "confidence": max_score,
                "sources": [{"title": c.get("title"), "content": c.get("content")[:200], "score": c.get("score")} for c in top_chunks[:3]],
                "decision": "suggest",  # 建议模式，人工确认后发送
            }

    async def generate_stream(
        self,
        query: str,
        top_chunks: list[dict],
        chat_history: list[dict] | None = None,
    ):
        """
        流式生成回复 — 返回异步迭代器，逐 token yield。
        用于 SSE 推送到前端。
        """
        if not top_chunks or top_chunks[0].get("score", 0) < settings.RAG_CONFIDENCE_MEDIUM:
            yield "抱歉，我暂时无法回答这个问题，正在为您转接人工客服。"
            return

        context = self._build_context(top_chunks[: settings.RAG_RERANK_TOP_K])
        messages = self._build_messages(query, context, chat_history)

        async for token in self.llm.chat_stream(messages, temperature=0.3, max_tokens=512):
            yield token
