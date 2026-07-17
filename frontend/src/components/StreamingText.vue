<template>
  <div class="streaming-text" v-html="renderContent(text)" />
</template>

<script setup>
import { marked } from 'marked'
defineProps({ text: String })
function renderContent(t) {
  if (!t) return ''
  try { return marked.parse(t, { breaks: true }) } catch { return t }
}
</script>

<style scoped>
.streaming-text { font-size: 14px; line-height: 1.6; word-break: break-word; }
.streaming-text::after {
  content: '|';
  animation: blink 1s infinite;
  color: #409EFF;
  font-weight: bold;
}
@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
</style>
