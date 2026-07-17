/**
 * SSE 客户端 — 订阅会话实时事件流
 * 参考 Chatwoot ActionCable 的频道设计
 */
export function subscribeToConversation(conversationId, callbacks = {}) {
  const token = localStorage.getItem('access_token')
  if (!token) return null

  const url = `/api/v1/conversations/${conversationId}/stream?token=${encodeURIComponent(token)}`
  const eventSource = new EventSource(url)

  eventSource.addEventListener('message.created', (e) => {
    const data = JSON.parse(e.data)
    callbacks.onMessage?.(data)
  })

  eventSource.addEventListener('ai_chunk', (e) => {
    const data = JSON.parse(e.data)
    callbacks.onAIChunk?.(data)
  })

  eventSource.addEventListener('ai_done', (e) => {
    const data = JSON.parse(e.data)
    callbacks.onAIDone?.(data)
  })

  eventSource.addEventListener('agent_action', (e) => {
    const data = JSON.parse(e.data)
    callbacks.onAgentAction?.(data)
  })

  eventSource.addEventListener('conversation.updated', (e) => {
    const data = JSON.parse(e.data)
    callbacks.onConversationUpdate?.(data)
  })

  eventSource.addEventListener('assignee.changed', (e) => {
    const data = JSON.parse(e.data)
    callbacks.onAssigneeChanged?.(data)
  })

  eventSource.addEventListener('handoff', (e) => {
    const data = JSON.parse(e.data)
    callbacks.onHandoff?.(data)
  })

  eventSource.addEventListener('sentiment_alert', (e) => {
    const data = JSON.parse(e.data)
    callbacks.onSentimentAlert?.(data)
  })

  eventSource.onerror = () => {
    eventSource.close()
    // 自动重连（指数退避由浏览器 EventSource 自带）
    callbacks.onError?.()
  }

  return eventSource
}

export function subscribeToAgent(agentId, callbacks = {}) {
  const token = localStorage.getItem('access_token')
  if (!token) return null

  const url = `/api/v1/agents/${agentId}/stream?token=${encodeURIComponent(token)}`
  const es = new EventSource(url)

  es.addEventListener('message.created', (e) => callbacks.onMessage?.(JSON.parse(e.data)))
  es.addEventListener('conversation.updated', (e) => callbacks.onConversationUpdate?.(JSON.parse(e.data)))
  es.onerror = () => { es.close(); callbacks.onError?.() }

  return es
}
