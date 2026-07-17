<template>
  <div v-if="!conversation" class="empty-chat">
    <div class="empty-icon">💬</div>
    <p>选择左侧会话开始聊天</p>
  </div>
  <div class="chat-window" v-else>
    <!-- 顶栏 -->
    <header class="chat-header">
      <div class="chat-header-left">
        <span class="chat-customer">{{ conversation.contact_name || '访客 #' + conversation.display_id }}</span>
        <span class="chat-status">{{ statusLabel(conversation.status) }}</span>
      </div>
      <el-button size="small" text type="danger" @click="handleResolve" v-if="conversation.status !== 'resolved'">结束会话</el-button>
    </header>

    <!-- 消息区 -->
    <div class="chat-messages" ref="msgContainer">
      <div v-if="msgStore.messages.length === 0 && !msgStore.isStreaming" class="chat-empty">
        <p>暂无消息，输入内容开始对话</p>
      </div>
      <MessageBubble
        v-for="msg in msgStore.messages"
        :key="msg.id"
        :message="msg"
        @refundOrder="(no) => { inputText = '退款 ' + no; handleSend() }"
        @queryOrder="(no) => { inputText = '查订单 ' + no; handleSend() }"
        @queryLogistics="(no) => { inputText = '查物流 ' + no; handleSend() }"
      />
      <!-- AI 流式输出 -->
      <div v-if="msgStore.aiThinking" class="msg-row left">
        <div class="bubble bubble-left thinking-bubble">
          <span class="dot"></span><span class="dot"></span><span class="dot"></span>
        </div>
      </div>
      <div v-if="msgStore.streamingContent" class="msg-row left">
        <div class="bubble bubble-left">{{ msgStore.streamingContent }}<span class="cursor">|</span></div>
      </div>
      <div ref="msgBottom"></div>
    </div>

    <!-- 输入区 -->
    <div class="chat-input">
      <div class="input-actions">
        <el-dropdown size="small" @command="(no) => handleSend('查订单 ' + no)" @visible-change="(v) => v && loadOrders()" >
          <el-button size="small" >查订单</el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item v-if="orderList.length === 0" disabled>暂无订单</el-dropdown-item>
              <el-dropdown-item v-for="o in orderList" :key="o.order_no" :command="o.order_no">{{ o.order_no }} · {{ o.product_name }}</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-dropdown size="small" @command="(no) => handleSend('查物流 ' + no)" @visible-change="(v) => v && loadOrders()" >
          <el-button size="small" >查物流</el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item v-if="shippedOrders.length === 0" disabled>暂无已发货订单</el-dropdown-item>
              <el-dropdown-item v-for="o in shippedOrders" :key="o.order_no" :command="o.order_no">{{ o.order_no }} · {{ o.product_name }}</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-dropdown size="small" @command="(no) => handleRefundOrder(no)" @visible-change="(v) => v && loadOrders()" >
          <el-button size="small" type="danger" >退款</el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item v-if="orderList.length === 0" disabled>暂无订单</el-dropdown-item>
              <el-dropdown-item v-for="o in orderList" :key="o.order_no" :command="o.order_no">{{ o.order_no }} · ¥{{ o.total_amount }}</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
      <div class="input-row">
        <el-input v-model="inputText" type="textarea" :rows="3" placeholder="输入消息... (Enter 发送)"
          @keydown.enter.exact.prevent="handleSend"  resize="none" />
        <el-button type="primary" @click="handleSend()" :disabled="!inputText.trim()" style="margin-left:8px; height:auto; min-height:64px;">发送</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessageStore } from '../stores/message'
import { useConversationStore } from '../stores/conversation'
import { api } from '../api/client'
import { subscribeToConversation } from '../utils/sse'
import { ElMessage, ElNotification } from 'element-plus'
import MessageBubble from '../components/MessageBubble.vue'

const route = useRoute()
const router = useRouter()
const msgStore = useMessageStore()
const convStore = useConversationStore()
const inputText = ref('')
const conversation = ref(null)
const msgContainer = ref(null)
const msgBottom = ref(null)
const orderList = ref([])
let sseConn = null

const shippedOrders = ref([])

onMounted(async () => {
  await loadConversation()
  await msgStore.fetchMessages(route.params.id)
  connectSSE()
  scrollToBottom()
})

onUnmounted(() => { if (sseConn) sseConn.close() })

watch(() => route.params.id, async (id) => {
  if (id) { await loadConversation(); await msgStore.fetchMessages(id); connectSSE(); scrollToBottom() }
})

async function loadConversation() {
  try { const r = await api.get(`/conversations/${route.params.id}`); conversation.value = r.data }
  catch (e) { /* */ }
}

function connectSSE() {
  if (sseConn) sseConn.close()
  const id = route.params.id
  sseConn = subscribeToConversation(id, {
    onMessage: (data) => {
      // 跳过 AI 自己的出站消息 — 流式响应已处理，避免重复
      if (data.sender_type === 'ai' && data.message_type === 'outgoing') return
      msgStore.upsertMessage(data, data.source_id); scrollToBottom()
    },
    onSentimentAlert: (data) => {
      const labels = { positive: '满意', neutral: '中性', negative: '不满', very_negative: '非常不满' }
      const label = labels[data.label] || data.label
      ElNotification({ title: '情感预警', message: `客户情绪: ${label}，得分: ${(data.score * 100).toFixed(0)}%${data.is_escalated ? '（已自动升级工单）' : ''}`, type: data.alert_level === 'critical' ? 'error' : 'warning', duration: 8000 })
    },
    onConversationUpdate: (d) => { if (conversation.value) conversation.value.status = d.status },
    onError: () => { msgStore.isStreaming = false; msgStore.aiThinking = false },
  })
}

async function handleSend(quickText) {
  if (typeof quickText === 'string') inputText.value = quickText
  const text = inputText.value.trim()
  if (!text) return
  inputText.value = ''
  await msgStore.sendMessage(route.params.id, text)
  scrollToBottom()
}

async function loadOrders() {
  try {
    const resp = await api.get('/agent/order/query-by-contact', { params: { contact_id: conversation.value?.contact_id } })
    orderList.value = resp.data.orders || []
    shippedOrders.value = orderList.value.filter(o => o.logistics_no && o.status === 'shipped')
  } catch (e) { /* */ }
}

async function handleRefundOrder(orderNo) { inputText.value = '退款 ' + orderNo; handleSend() }
async function handleResolve() {
  try {
    await api.post(`/conversations/${route.params.id}/resolve`)
    ElMessage.success('会话已结束')
    const idx = convStore.conversations.findIndex(c => c.id === route.params.id)
    if (idx >= 0) convStore.conversations.splice(idx, 1)
    // 清空当前会话，跳转空白
    conversation.value = null
    msgStore.messages = []
    msgStore.streamingContent = ''
    msgStore.isStreaming = false
    router.push('/chat/empty')
  } catch (e) { /* */ }
}

function scrollToBottom() { nextTick(() => { msgBottom.value?.scrollIntoView({ behavior: 'smooth' }) }) }
function statusLabel(s) { return { open: '进行中', pending: '待接入', resolved: '已结束', snoozed: '暂缓' }[s] || s }
</script>

<style scoped>
.empty-chat { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; background: #f5f5f5; color: #bbb; }
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.chat-window { display: flex; flex-direction: column; height: 100%; background: #f5f5f5; }
.chat-header { display: flex; align-items: center; justify-content: space-between; padding: 10px 16px; background: #fff; border-bottom: 1px solid #e8e8e8; flex-shrink: 0; }
.chat-header-left { display: flex; align-items: center; gap: 8px; }
.chat-customer { font-size: 15px; font-weight: 500; color: #333; }
.chat-status { font-size: 12px; color: #999; }
.chat-messages { flex: 1; overflow-y: auto; padding: 16px 0; }
.chat-empty { text-align: center; color: #bbb; margin-top: 120px; font-size: 14px; }
.chat-input { padding: 8px 16px 12px; background: #fff; border-top: 1px solid #e8e8e8; flex-shrink: 0; }
.input-actions { display: flex; gap: 6px; margin-bottom: 8px; }
.input-row { display: flex; align-items: stretch; }
.thinking-bubble { display: flex; gap: 4px; align-items: center; padding: 12px 16px; }
.dot { width: 6px; height: 6px; border-radius: 50%; background: #bbb; animation: blink 1.4s infinite ease-in-out both; }
.dot:nth-child(2) { animation-delay: .2s; }
.dot:nth-child(3) { animation-delay: .4s; }
@keyframes blink { 0%,80%,100% { opacity: 0 } 40% { opacity: 1 } }
.cursor { animation: blink 1s infinite; }
</style>
