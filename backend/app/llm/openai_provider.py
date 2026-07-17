"""
OpenAI 提供商实现
"""
from typing import AsyncIterator
from openai import AsyncOpenAI
from app.llm.base import BaseLLMProvider, ChatMessage, ChatResponse, EmbeddingResponse
from app.core.config import settings


class OpenAIProvider(BaseLLMProvider):
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY or "sk-placeholder",
            base_url=settings.OPENAI_BASE_URL,
        )
        self.model = settings.LLM_MODEL
        self.embedding_model = settings.EMBEDDING_MODEL

    @property
    def provider_name(self) -> str:
        return "openai"

    async def chat(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.3,
        max_tokens: int = 2048,
        tools: list[dict] | None = None,
    ) -> ChatResponse:
        msgs = [{"role": m.role, "content": m.content} for m in messages]
        kwargs = {
            "model": self.model,
            "messages": msgs,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools

        resp = await self.client.chat.completions.create(**kwargs)
        choice = resp.choices[0]
        return ChatResponse(
            content=choice.message.content or "",
            model=resp.model,
            usage={
                "prompt_tokens": resp.usage.prompt_tokens if resp.usage else 0,
                "completion_tokens": resp.usage.completion_tokens if resp.usage else 0,
            },
        )

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        msgs = [{"role": m.role, "content": m.content} for m in messages]
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=msgs,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def embed(self, texts: list[str]) -> EmbeddingResponse:
        resp = await self.client.embeddings.create(
            model=self.embedding_model,
            input=texts,
        )
        embeddings = [d.embedding for d in resp.data]
        return EmbeddingResponse(
            embeddings=embeddings,
            model=resp.model,
            dimensions=len(embeddings[0]) if embeddings else 0,
        )
