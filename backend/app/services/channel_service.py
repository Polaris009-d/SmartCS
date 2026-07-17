"""
渠道服务 — 根据 channel_type 返回对应的 Channel Adapter
"""
from app.channels.base import ChannelAdapter
from app.channels.web_widget import WebWidgetChannel

_CHANNEL_REGISTRY: dict[str, ChannelAdapter] = {
    "web_widget": WebWidgetChannel(),
}


def get_channel_adapter(channel_type: str) -> ChannelAdapter:
    """根据渠道类型获取适配器"""
    adapter = _CHANNEL_REGISTRY.get(channel_type)
    if adapter is None:
        raise ValueError(f"Unknown channel type: {channel_type}")
    return adapter


def register_channel_adapter(channel_type: str, adapter: ChannelAdapter):
    """注册自定义渠道适配器（扩展用）"""
    _CHANNEL_REGISTRY[channel_type] = adapter
