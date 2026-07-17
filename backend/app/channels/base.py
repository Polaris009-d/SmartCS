"""
渠道适配器抽象基类 — 参考 Chatwoot Channel 多态设计
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class IncomingMessage:
    """渠道无关的统一入站消息格式"""
    content: str
    content_type: str = "text"
    source_id: str | None = None  # 渠道内消息 ID（去重）
    sender_name: str | None = None
    sender_email: str | None = None
    sender_phone: str | None = None
    raw_data: dict | None = None  # 原始数据（调试/审计）
    content_attributes: dict | None = None  # 附件、卡片等


class ChannelAdapter(ABC):
    """
    渠道适配器基类。
    每个渠道实现此接口，负责：
      1. 将渠道特定格式转换为统一 IncomingMessage
      2. 将统一格式转换为渠道特定出站格式
    """

    @property
    @abstractmethod
    def channel_type(self) -> str:
        """返回渠道类型标识：web_widget | api | email"""
        ...

    @abstractmethod
    def convert_incoming(self, raw_payload: Any) -> IncomingMessage:
        """将渠道原始消息转换为统一格式"""
        ...

    @abstractmethod
    def format_outgoing(self, content: str, content_type: str, **kwargs) -> dict:
        """将统一格式转换为渠道特定的出站格式"""
        ...
