"""
Web Widget 渠道适配器 — 网页嵌入聊天
"""
from app.channels.base import ChannelAdapter, IncomingMessage


class WebWidgetChannel(ChannelAdapter):
    """
    Web Widget 是 SmartCS 最主要的客户接入方式。
    客户通过网页上的聊天窗口发送消息。
    """

    @property
    def channel_type(self) -> str:
        return "web_widget"

    def convert_incoming(self, raw_payload: dict) -> IncomingMessage:
        """
        将 Web Widget 前端发来的 JSON 转换为统一格式。

        raw_payload 示例:
        {
            "content": "我想咨询尺码",
            "content_type": "text",
            "contact_name": "张三",
            "source_id": "msg-uuid-xxx"
        }
        """
        return IncomingMessage(
            content=raw_payload.get("content", ""),
            content_type=raw_payload.get("content_type", "text"),
            source_id=raw_payload.get("source_id"),
            sender_name=raw_payload.get("contact_name"),
            sender_email=raw_payload.get("contact_email"),
            sender_phone=raw_payload.get("contact_phone"),
            raw_data=raw_payload,
            content_attributes=raw_payload.get("content_attributes"),
        )

    def format_outgoing(self, content: str, content_type: str = "text", **kwargs) -> dict:
        """
        将内部消息格式转换为 Web Widget 可以消费的格式。
        这个方法的输出会被放入 SSE message.created 事件的 data 中。
        """
        return {
            "content": content,
            "content_type": content_type,
            "sender_type": kwargs.get("sender_type", "ai"),
            "message_type": kwargs.get("message_type", "outgoing"),
        }
