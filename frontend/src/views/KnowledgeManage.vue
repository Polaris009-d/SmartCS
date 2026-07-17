<template>
  <div class="knowledge-page">
    <div class="knowledge-toolbar">
      <el-input v-model="searchQuery" placeholder="搜索知识库..." clearable @keyup.enter="handleSearch" style="width:320px">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-upload :http-request="handleUpload" :show-file-list="false" accept=".txt,.md" :disabled="uploading">
        <el-button type="primary" :loading="uploading">
          <el-icon><Upload /></el-icon>{{ uploading ? '上传中...' : '上传文档（TXT / MD）' }}
        </el-button>
      </el-upload>
    </div>

    <!-- 搜索结果 -->
    <div v-if="searchResults.length > 0" class="search-results">
      <h4>搜索结果 ({{ searchResults.length }})</h4>
      <el-card v-for="item in searchResults" :key="item.id" class="result-card" shadow="hover">
        <template #header>
          <div class="result-header">
            <span class="result-title">{{ item.title }}</span>
            <el-tag size="small">{{ item.source_type }}</el-tag>
            <span class="result-score">相关性: {{ (item.score * 100).toFixed(0) }}%</span>
          </div>
        </template>
        <p>{{ item.content.substring(0, 300) }}...</p>
      </el-card>
    </div>

    <!-- 文档列表 -->
    <div v-else>
      <h4>知识库文档</h4>
      <el-table :data="documents" stripe v-loading="loading">
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="source_type" label="类型" width="120" />
        <el-table-column prop="created_at" label="日期" width="180" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button type="danger" size="small" text @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api/client'
import { ElMessage } from 'element-plus'

const searchQuery = ref('')
const searchResults = ref([])
const documents = ref([])
const loading = ref(false)
const uploading = ref(false)

onMounted(loadDocuments)

async function loadDocuments() {
  loading.value = true
  try {
    const resp = await api.get('/knowledge/documents')
    documents.value = resp.data
  } catch (e) { /* ignore */ }
  finally { loading.value = false }
}

async function handleSearch() {
  if (!searchQuery.value.trim()) return
  try {
    const resp = await api.get('/knowledge/search', { params: { q: searchQuery.value, top_k: 10 } })
    searchResults.value = resp.data
  } catch (e) { ElMessage.error('搜索失败') }
}

async function handleUpload({ file }) {
  uploading.value = true
  const formData = new FormData()
  formData.append('file', file)
  formData.append('source_type', 'faq')
  try {
    const resp = await api.post('/knowledge/documents', formData)
    ElMessage.success(`上传成功：${resp.data.inserted} 个片段已入库`)
    searchResults.value = []
    await loadDocuments()
  } catch (e) {
    ElMessage.error('上传失败：' + (e.response?.data?.detail || e.message))
  } finally {
    uploading.value = false
  }
}

async function handleDelete(id) {
  try {
    await api.delete(`/knowledge/documents/${id}`)
    ElMessage.success('已删除')
    await loadDocuments()
  } catch (e) { ElMessage.error('删除失败') }
}
</script>

<style scoped>
.knowledge-page { padding: 16px; overflow-y: auto; height: 100%; }
.knowledge-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.search-results { margin-top: 10px; }
.result-card { margin-bottom: 12px; }
.result-header { display: flex; align-items: center; gap: 8px; }
.result-title { font-weight: 600; flex: 1; }
.result-score { color: #67c23a; font-size: 12px; }
</style>
