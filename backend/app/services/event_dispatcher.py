"""
事件分发器 — 参考 Chatwoot EventDispatcher (Wisper)
消息创建后分发到不同监听器：SSE 推送、Webhook、自动化规则
"""
import asyncio
from typing import Any, Callable, Coroutine
from collections import defaultdict

EventHandler = Callable[[str, dict[str, Any]], Coroutine[Any, Any, None]]


class EventDispatcher:
    """
    轻量级事件分发器。
    支持按事件类型注册处理器，dispatch 时并发执行所有匹配的处理器。
    参考 Chatwoot: Rails.configuration.dispatcher + Wisper
    """

    def __init__(self):
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def on(self, event_type: str, handler: EventHandler):
        """注册事件处理器"""
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)

    def off(self, event_type: str, handler: EventHandler):
        """移除事件处理器"""
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

    async def dispatch(self, event_type: str, data: dict[str, Any]):
        """
        异步分发事件。所有匹配的处理器并发执行。
        单个处理器异常不会影响其他处理器。
        """
        handlers = self._handlers.get(event_type, [])
        if not handlers:
            return
        tasks = [handler(event_type, data) for handler in handlers]
        await asyncio.gather(*tasks, return_exceptions=True)


# 全局单例
event_dispatcher = EventDispatcher()
