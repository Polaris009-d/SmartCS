import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api/client'

export const useMessageStore = defineStore('message', () => {
  const messages = ref([])
  const streamingContent = ref('')
  const isStreaming = ref(false)
  const aiThinking = ref(false)

  async function fetchMessages(conversationId, page = 1) {
    const resp = await api.get(`/conversations/${conversationId}/messages`, {
      params: { page, page_size: 50 },
    })
    messages.value = resp.data.items
    return resp.data
  }

  function upsertMessage(msg, sourceId) {
    // 如果已有同 source_id 的临时消息则替换，否则追加
    const idx = messages.value.findIndex(m => m.source_id === sourceId)
    if (idx >= 0) {
      messages.value[idx] = msg
    } else {
      messages.value.push(msg)
    }
    return idx < 0  // true = 新增, false = 替换
  }

  async function sendMessage(conversationId, content, messageType = 'incoming') {
    // 乐观添加用户消息，带临时 source_id 用于去重
    const tempSourceId = 'temp-' + crypto.randomUUID()
    const tempMsg = {
      id: 'temp-' + Date.now(),
      source_id: tempSourceId,
      conversation_id: conversationId,
      message_type: messageType,
      content_type: 'text',
      content,
      sender_type: messageType === 'incoming' ? 'contact' : 'agent',
      created_at: new Date().toISOString(),
    }
    messages.value.push(tempMsg)

    isStreaming.value = true
    streamingContent.value = ''
    aiThinking.value = true

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`/api/v1/conversations/${conversationId}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          content,
          message_type: messageType,
          content_type: 'text',
          source_id: tempSourceId,
        }),
      })

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      let currentEvent = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim()
          }
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (currentEvent === 'ai_chunk') {
                streamingContent.value += data.chunk || ''
                aiThinking.value = false
              } else if (currentEvent === 'ai_done') {
                messages.value.push({
                  id: 'ai-' + Date.now(),
                  conversation_id: conversationId,
                  message_type: 'outgoing',
                  content_type: 'text',
                  content: data.full_content || streamingContent.value,
                  sender_type: 'ai',
                  ai_confidence: data.confidence,
                  content_attributes: { sources: data.sources || [] },
                  created_at: new Date().toISOString(),
                })
                streamingContent.value = ''
                isStreaming.value = false
                aiThinking.value = false
              } else if (currentEvent === 'agent_action') {
                messages.value.push({
                  id: 'agent-' + Date.now(),
                  conversation_id: conversationId,
                  message_type: 'outgoing',
                  content_type: 'agent_action',
                  content: data.message,
                  sender_type: 'ai',
                  content_attributes: data,
                  created_at: new Date().toISOString(),
                })
                streamingContent.value = ''
                isStreaming.value = false
                aiThinking.value = false
              } else if (currentEvent === 'handoff') {
                isStreaming.value = false
                aiThinking.value = false
              } else if (currentEvent === 'thinking') {
                // AI 开始思考
              }
            } catch (e) { /* ignore parse errors */ }
          }
        }
      }
    } catch (e) {
      messages.value.push({
        id: 'err-' + Date.now(),
        conversation_id: conversationId,
        message_type: 'activity',
        content_type: 'text',
        content: 'AI 回复失败，请重试或转人工客服',
        sender_type: 'system',
        created_at: new Date().toISOString(),
      })
      isStreaming.value = false
      aiThinking.value = false
    }
  }

  return { messages, streamingContent, isStreaming, aiThinking, fetchMessages, sendMessage, upsertMessage }
})
