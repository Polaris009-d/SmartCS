<template>
  <!-- 系统消息：居中 -->
  <div v-if="message.message_type === 'activity'" class="msg-row center">
    <span class="sys-msg">{{ message.content }}</span>
  </div>

  <!-- AI/Agent 卡片 -->
  <div v-else-if="message.content_type === 'agent_action'" class="msg-row left">
    <div class="bubble ai-bubble">
      <AgentActionCard :data="message.content_attributes"
        @refundOrder="(no) => $emit('refundOrder', no)"
        @queryOrder="(no) => $emit('queryOrder', no)"
        @queryLogistics="(no) => $emit('queryLogistics', no)" />
    </div>
  </div>

  <!-- 普通消息：客户左 / AI客服右 -->
  <div v-else :class="['msg-row', isRight ? 'right' : 'left']">
    <div :class="['bubble', isRight ? 'bubble-right' : 'bubble-left']">
      <div class="msg-text" v-if="message.content_type !== 'agent_action'">{{ message.content }}</div>
      <div class="msg-time">{{ fmtTime(message.created_at) }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import AgentActionCard from './AgentActionCard.vue'

const props = defineProps({ message: Object })
defineEmits(['refundOrder', 'queryOrder', 'queryLogistics'])

const isRight = computed(() => props.message.message_type === 'incoming' || props.message.sender_type === 'contact')

function fmtTime(t) {
  if (!t) return ''
  return new Date(t).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.msg-row { display: flex; margin: 8px 16px; }
.msg-row.left { justify-content: flex-start; }
.msg-row.right { justify-content: flex-end; }
.msg-row.center { justify-content: center; }

.bubble { max-width: 70%; padding: 10px 14px; border-radius: 12px; font-size: 14px; line-height: 1.6; word-break: break-word; position: relative; }
.bubble-left { background: #fff; border: 1px solid #eee; border-bottom-left-radius: 4px; }
.bubble-right { background: #409EFF; color: #fff; border-bottom-right-radius: 4px; }
.ai-bubble { background: #fff; border: 1px solid #e8f3ff; padding: 8px; max-width: 80%; }

.msg-text { white-space: pre-wrap; }
.msg-time { font-size: 10px; margin-top: 4px; opacity: 0.5; text-align: right; }
.bubble-left .msg-time { color: #999; }

.sys-msg { font-size: 12px; color: #bbb; background: none; padding: 2px 8px; }
</style>
