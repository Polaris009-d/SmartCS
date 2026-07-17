"""
LLM 提供商抽象基类
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator


@dataclass
class ChatMessage:
    role: str  # system | user | assistant
    content: str


@dataclass
class ChatResponse:
    content: str
    model: str = ""
    usage: dict = field(default_factory=dict)  # prompt_tokens, completion_tokens


@dataclass
class EmbeddingResponse:
    embeddings: list[list[float]]
    model: str = ""
    dimensions: int = 0


class BaseLLMProvider(ABC):
    """LLM 提供商抽象 — 所有提供商实现此接口"""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...

    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.3,
        max_tokens: int = 2048,
        tools: list[dict] | None = None,
    ) -> ChatResponse:
        """发送对话请求，返回完整回复"""
        ...

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """发送对话请求，返回流式 token 迭代器"""
        ...

    @abstractmethod
    async def embed(self, texts: list[str]) -> EmbeddingResponse:
        """批量文本向量化"""
        ...
