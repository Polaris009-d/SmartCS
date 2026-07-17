"""
SSE Manager — 管理 SSE 订阅者的 asyncio.Queue，实现 per-conversation 实时推送。
参考 Chatwoot ActionCable 的频道模型，但用 SSE + asyncio.Queue 实现。
"""
import asyncio
import json
import time
from collections import defaultdict


class SSEManager:
    """
    每个 conversation_id 维护一个订阅者队列列表，
    publish() 时将事件 fan-out 到所有订阅者。
    """

    def __init__(self):
        self._subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)
        self._agent_subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)
        self._lock: asyncio.Lock = asyncio.Lock()

    async def subscribe(self, conversation_id: str) -> asyncio.Queue:
        """订阅某个会话的 SSE 事件，返回一个 asyncio.Queue"""
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._subscribers[conversation_id].append(queue)
        return queue

    async def unsubscribe(self, conversation_id: str, queue: asyncio.Queue):
        """取消订阅"""
        async with self._lock:
            subs = self._subscribers.get(conversation_id, [])
            if queue in subs:
                subs.remove(queue)
            if not subs:
                self._subscribers.pop(conversation_id, None)

    async def subscribe_agent(self, agent_id: str) -> asyncio.Queue:
        """订阅 Agent 全局通知（新会话分配等）"""
        queue: asyncio.Queue = asyncio.Queue(maxsize=50)
        async with self._lock:
            self._agent_subscribers[agent_id].append(queue)
        return queue

    async def unsubscribe_agent(self, agent_id: str, queue: asyncio.Queue):
        """取消 Agent 全局订阅"""
        async with self._lock:
            subs = self._agent_subscribers.get(agent_id, [])
            if queue in subs:
                subs.remove(queue)
            if not subs:
                self._agent_subscribers.pop(agent_id, None)

    async def publish(self, conversation_id: str, event_type: str, data: dict):
        """向会话的所有订阅者推送事件"""
        async with self._lock:
            queues = list(self._subscribers.get(conversation_id, []))
        await self._fan_out(queues, event_type, data)

    async def publish_agent(self, agent_id: str, event_type: str, data: dict):
        """向特定客服推送全局事件"""
        async with self._lock:
            queues = list(self._agent_subscribers.get(agent_id, []))
        await self._fan_out(queues, event_type, data)

    async def publish_agent_broadcast(self, event_type: str, data: dict):
        """向所有在线客服推送事件"""
        async with self._lock:
            all_queues = []
            for queues in self._agent_subscribers.values():
                all_queues.extend(queues)
        await self._fan_out(all_queues, event_type, data)

    async def _fan_out(self, queues: list[asyncio.Queue], event_type: str, data: dict):
        """将事件推送到一组队列"""
        if not queues:
            return
        payload = f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
        for queue in queues:
            try:
                await asyncio.wait_for(queue.put(payload), timeout=1.0)
            except (asyncio.TimeoutError, asyncio.QueueFull):
                pass  # 慢消费者丢弃

    async def send_keepalive(self):
        """向所有订阅者发送心跳"""
        async with self._lock:
            all_queues = []
            for queues in self._subscribers.values():
                all_queues.extend(queues)
        await self._fan_out(all_queues, "keepalive", {"ts": time.time()})


# 全局单例
sse_manager = SSEManager()
