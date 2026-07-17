<template>
  <div class="ticket-page">
    <div class="page-header">
      <h3>工单管理</h3>
      <el-button type="primary" size="small" @click="showCreate = true">
        <el-icon><Plus /></el-icon>创建工单
      </el-button>
    </div>

    <div class="filters">
      <el-select v-model="filterStatus" placeholder="状态筛选" clearable size="small" @change="loadList">
        <el-option label="待处理" value="open" />
        <el-option label="处理中" value="in_progress" />
        <el-option label="已解决" value="resolved" />
        <el-option label="已关闭" value="closed" />
      </el-select>
      <el-select v-model="filterType" placeholder="类型筛选" clearable size="small" @change="loadList">
        <el-option label="退款" value="refund" />
        <el-option label="投诉" value="complaint" />
        <el-option label="升级" value="escalation" />
      </el-select>
    </div>

    <el-table :data="tickets" stripe v-loading="loading">
      <el-table-column prop="subject" label="主题" min-width="200" />
      <el-table-column prop="ticket_type" label="类型" width="100">
        <template #default="{ row }">
          <el-tag :type="typeColor(row.ticket_type)" size="small">{{ typeLabel(row.ticket_type) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="priority" label="优先级" width="80">
        <template #default="{ row }">
          <el-tag :type="priorityColor(row.priority)" size="small">{{ row.priority }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusColor(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">{{ fmt(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="handleAssign(row)">分配</el-button>
          <el-button v-if="row.status === 'open' || row.status === 'in_progress'" size="small" text type="success" @click="handleResolve(row.id)">解决</el-button>
          <el-button size="small" text type="info" @click="handleClose(row.id)">关闭</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建工单对话框 -->
    <el-dialog v-model="showCreate" title="创建工单" width="450px">
      <el-form :model="form" label-position="top">
        <el-form-item label="主题">
          <el-input v-model="form.subject" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.ticket_type" style="width:100%">
            <el-option label="退款" value="refund" />
            <el-option label="地址修改" value="address_change" />
            <el-option label="投诉" value="complaint" />
            <el-option label="升级" value="escalation" />
          </el-select>
        </el-form-item>
        <el-form-item label="客户ID">
          <el-input v-model="form.customer_id" placeholder="UUID" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="form.priority" style="width:100%">
            <el-option label="普通" value="normal" />
            <el-option label="高" value="high" />
            <el-option label="紧急" value="urgent" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { api } from '../api/client'
import { ElMessage, ElMessageBox } from 'element-plus'

const tickets = ref([])
const loading = ref(false)
const filterStatus = ref('')
const filterType = ref('')
const showCreate = ref(false)
const form = reactive({ subject: '', ticket_type: 'refund', customer_id: '', priority: 'normal', description: '' })

onMounted(loadList)

async function loadList() {
  loading.value = true
  try {
    const params = {}
    if (filterStatus.value) params.status = filterStatus.value
    if (filterType.value) params.ticket_type = filterType.value
    const resp = await api.get('/tickets', { params })
    tickets.value = resp.data.items
  } catch (e) { /* ignore */ }
  finally { loading.value = false }
}

async function handleCreate() {
  try {
    await api.post('/tickets', form)
    ElMessage.success('工单创建成功')
    showCreate.value = false
    loadList()
  } catch (e) { ElMessage.error('创建失败') }
}

async function handleAssign(row) {
  try {
    const { value } = await ElMessageBox.prompt('输入客服ID (UUID)', '分配工单')
    await api.post(`/tickets/${row.id}/assign`, { user_id: value })
    ElMessage.success('已分配')
    loadList()
  } catch (e) { /* cancel */ }
}

async function handleResolve(id) {
  await api.patch(`/tickets/${id}`, { status: 'resolved' })
  ElMessage.success('已解决')
  loadList()
}

async function handleClose(id) {
  await api.patch(`/tickets/${id}`, { status: 'closed' })
  ElMessage.success('已关闭')
  loadList()
}

function typeColor(t) { return { refund: 'danger', complaint: 'warning', escalation: 'danger', address_change: 'info' }[t] || '' }
function typeLabel(t) { return { refund: '退款', complaint: '投诉', escalation: '升级', address_change: '地址修改' }[t] || t }
function priorityColor(p) { return { low: 'info', normal: '', high: 'warning', urgent: 'danger' }[p] || '' }
function statusColor(s) { return { open: 'warning', in_progress: 'info', resolved: 'success', closed: '' }[s] || '' }
function statusLabel(s) { return { open: '待处理', in_progress: '处理中', resolved: '已解决', closed: '已关闭' }[s] || s }
function fmt(t) { return t ? new Date(t).toLocaleString('zh-CN') : '' }
</script>

<style scoped>
.ticket-page { padding: 16px; overflow-y: auto; height: 100%; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.page-header h3 { margin: 0; }
.filters { display: flex; gap: 12px; margin-bottom: 12px; }
</style>
