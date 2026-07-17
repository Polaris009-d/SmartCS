import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api/client'

export const useConversationStore = defineStore('conversation', () => {
  const conversations = ref([])
  const currentId = ref(null)
  const loading = ref(false)
  const filters = ref({ status: '', inbox_id: '' })

  async function fetchList(opts = {}) {
    loading.value = true
    try {
      if (opts.status !== undefined) filters.value.status = opts.status
      const params = { page: opts.page || 1, page_size: 20, ...filters.value }
      if (params.status === 'all') params.status = ''
      // 去掉空值
      Object.keys(params).forEach(k => { if (!params[k] && params[k] !== 0) delete params[k] })
      const resp = await api.get('/conversations', { params })
      conversations.value = resp.data.items
      return resp.data
    } finally {
      loading.value = false
    }
  }

  async function createConversation(inboxId, title) {
    const resp = await api.post('/conversations', {
      inbox_id: inboxId,
      title: title || '新会话',
    })
    return resp.data
  }

  async function updateConversation(id, data) {
    const resp = await api.patch(`/conversations/${id}`, data)
    return resp.data
  }

  async function resolveConversation(id) {
    await api.post(`/conversations/${id}/resolve`)
  }

  async function assignConversation(id, agentId) {
    await api.post(`/conversations/${id}/assign`, null, { params: { agent_id: agentId } })
  }

  function setCurrent(id) {
    currentId.value = id
  }

  return { conversations, currentId, loading, filters, fetchList, createConversation, updateConversation, resolveConversation, assignConversation, setCurrent }
})
