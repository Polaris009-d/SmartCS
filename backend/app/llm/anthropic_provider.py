"""
Anthropic Claude 提供商实现
"""
from typing import AsyncIterator
from anthropic import AsyncAnthropic
from app.llm.base import BaseLLMProvider, ChatMessage, ChatResponse, EmbeddingResponse
from app.core.config import settings


class AnthropicProvider(BaseLLMProvider):
    def __init__(self):
        self.client = AsyncAnthropic(
            api_key=settings.ANTHROPIC_API_KEY or "sk-ant-placeholder",
        )
        self.model = settings.LLM_MODEL

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def _to_anthropic_messages(self, messages: list[ChatMessage]) -> tuple[str | None, list[dict]]:
        """将通用消息格式转换为 Anthropic 格式，分离 system 消息"""
        system_content = None
        api_msgs = []
        for m in messages:
            if m.role == "system":
                system_content = m.content
            else:
                api_msgs.append({"role": m.role, "content": m.content})
        return system_content, api_msgs

    async def chat(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.3,
        max_tokens: int = 2048,
        tools: list[dict] | None = None,
    ) -> ChatResponse:
        system_content, api_msgs = self._to_anthropic_messages(messages)
        kwargs = {
            "model": self.model,
            "messages": api_msgs,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_content:
            kwargs["system"] = system_content

        resp = await self.client.messages.create(**kwargs)
        # 获取文本内容
        content = ""
        for block in resp.content:
            if block.type == "text":
                content += block.text
        return ChatResponse(
            content=content,
            model=resp.model,
            usage={
                "prompt_tokens": resp.usage.input_tokens if resp.usage else 0,
                "completion_tokens": resp.usage.output_tokens if resp.usage else 0,
            },
        )

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        system_content, api_msgs = self._to_anthropic_messages(messages)
        kwargs = {
            "model": self.model,
            "messages": api_msgs,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_content:
            kwargs["system"] = system_content

        async with self.client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text

    async def embed(self, texts: list[str]) -> EmbeddingResponse:
        # Anthropic 不提供 Embedding API，使用 OpenAI 兼容接口作为降级
        # 实际使用时可通过配置 EMBEDDING_PROVIDER 独立选择
        raise NotImplementedError(
            "Anthropic does not provide Embedding API. Set EMBEDDING_PROVIDER=openai or local"
        )
