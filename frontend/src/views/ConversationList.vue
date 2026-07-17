<template>
  <div class="conv-list">
    <div class="conv-search">
      <el-input v-model="searchText" placeholder="搜索会话..." size="small" clearable prefix-icon="Search" />
    </div>
    <div class="conv-filters">
      <el-radio-group v-model="filterStatus" size="small" @change="loadList">
        <el-radio-button value="all">全部</el-radio-button>
        <el-radio-button value="pending"><span class="dot pending"></span>待接入</el-radio-button>
        <el-radio-button value="open"><span class="dot open"></span>进行中</el-radio-button>
        <el-radio-button value="resolved"><span class="dot resolved"></span>已结束</el-radio-button>
      </el-radio-group>
    </div>
    <div class="conv-create">
      <el-button type="primary" size="small" @click="showCreate = true" style="width:100%">+ 新建会话</el-button>
    </div>
    <div class="conv-items" v-loading="loading">
      <div v-for="c in filteredList" :key="c.id"
        :class="['conv-card', { active: activeId === c.id }]"
        @click="$router.push(`/chat/${c.id}`)">
        <div class="conv-card-top">
          <span class="status-icon" :class="c.status"></span>
          <span class="conv-name">{{ c.contact_name || '访客 #' + c.display_id }}</span>
          <span class="conv-time">{{ fmtTime(c.last_activity_at) }}</span>
        </div>
        <div class="conv-card-bottom">
          <span class="conv-title">{{ c.title || '会话 #' + c.display_id }}</span>
          <span class="conv-preview" v-if="c.last_message">{{ c.last_message }}</span>
        </div>
      </div>
      <el-empty v-if="!loading && filteredList.length === 0" description="暂无会话" :image-size="60" />
    </div>

    <el-dialog v-model="showCreate" title="新建会话" width="360px">
      <el-form :model="newConv" label-position="top">
        <el-form-item label="标题"><el-input v-model="newConv.title" size="small" /></el-form-item>
        <el-form-item label="渠道">
          <el-select v-model="newConv.inbox_id" size="small" style="width:100%">
            <el-option v-for="ib in inboxes" :key="ib.id" :label="ib.name" :value="ib.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button size="small" @click="showCreate = false">取消</el-button>
        <el-button size="small" type="primary" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useConversationStore } from '../stores/conversation'
import { api } from '../api/client'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const convStore = useConversationStore()
const searchText = ref('')
const filterStatus = ref('')
const loading = ref(false)
const showCreate = ref(false)
const inboxes = ref([])
const newConv = reactive({ title: '', inbox_id: '' })
const activeId = computed(() => route.params.id || '')

const filteredList = computed(() => {
  if (!searchText.value) return convStore.conversations
  const kw = searchText.value.toLowerCase()
  return convStore.conversations.filter(c =>
    (c.title || '').toLowerCase().includes(kw) ||
    (c.contact_name || '').toLowerCase().includes(kw) ||
    String(c.display_id).includes(kw)
  )
})

onMounted(async () => {
  await loadList()
  try { const r = await api.get('/inboxes'); inboxes.value = r.data; if (r.data.length) newConv.inbox_id = r.data[0].id } catch (e) { /* */ }
})

async function loadList() {
  loading.value = true
  try { await convStore.fetchList({ status: filterStatus.value, page: 1 }) }
  catch (e) { /* */ }
  finally { loading.value = false }
}

async function handleCreate() {
  if (!newConv.inbox_id) return ElMessage.warning('请选择渠道')
  try {
    const conv = await convStore.createConversation(newConv.inbox_id, newConv.title)
    showCreate.value = false
    router.push(`/chat/${conv.id}`)
  } catch (e) { ElMessage.error('创建失败') }
}

function fmtTime(t) {
  if (!t) return ''
  const d = new Date(t), now = new Date(), diff = now - d
  if (diff < 6e4) return '刚刚'
  if (diff < 36e5) return Math.floor(diff / 6e4) + '分钟前'
  if (diff < 864e5) return Math.floor(diff / 36e5) + '小时前'
  return d.toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.conv-list { display: flex; flex-direction: column; height: 100%; background: #fafafa; }
.conv-search { padding: 12px 12px 0; }
.conv-filters { padding: 8px 12px; }
.conv-create { padding: 0 12px 8px; }
.conv-items { flex: 1; overflow-y: auto; padding: 0 12px 12px; }
.conv-card { padding: 12px; margin-bottom: 4px; background: #fff; border-radius: 8px; cursor: pointer; border: 1px solid transparent; transition: all .15s; }
.conv-card:hover { border-color: #e0e0e0; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
.conv-card.active { border-color: #409EFF; background: #ecf5ff; }
.conv-card-top { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.conv-name { font-size: 14px; font-weight: 500; color: #333; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.conv-time { font-size: 11px; color: #999; }
.conv-card-bottom { display: flex; flex-direction: column; }
.conv-title { font-size: 12px; color: #666; }
.conv-preview { font-size: 12px; color: #aaa; margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.status-icon { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.status-icon.pending { background: #909399; }
.status-icon.open { background: #67c23a; }
.status-icon.resolved { background: #409EFF; }
.status-icon.snoozed { background: #e6a23c; }
.dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%; margin-right: 2px; vertical-align: middle; }
.dot.pending { background: #909399; }
.dot.open { background: #67c23a; }
.dot.resolved { background: #409EFF; }
</style>
