<template>
  <div class="dashboard-page">
    <div class="page-header">
      <h3>绩效看板</h3>
      <el-select v-model="days" size="small" style="width:120px" @change="loadData">
        <el-option :value="1" label="今天" />
        <el-option :value="7" label="近7天" />
        <el-option :value="30" label="近30天" />
      </el-select>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ data.conversations?.total || 0 }}</div>
          <div class="stat-label">总会话数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card ai">
          <div class="stat-value">{{ data.conversations?.ai_handling_rate || 0 }}%</div>
          <div class="stat-label">AI 处理率</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ data.messages?.total || 0 }}</div>
          <div class="stat-label">总消息数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ data.conversations?.human_handled || 0 }}</div>
          <div class="stat-label">人工处理</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表 -->
    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>会话状态分布</template>
          <div ref="statusChart" style="height:300px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>消息发送者分布</template>
          <div ref="senderChart" style="height:300px"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Agent 操作统计 -->
    <el-card shadow="hover" style="margin-top:16px">
      <template #header>Agent 操作统计</template>
      <el-table :data="agentOps" stripe size="small">
        <el-table-column prop="type" label="Agent 类型" width="160" />
        <el-table-column prop="success" label="成功" width="100" />
        <el-table-column prop="rejected" label="拒绝" width="100" />
        <el-table-column prop="error" label="错误" width="100" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { api } from '../api/client'
import * as echarts from 'echarts'

const days = ref(7)
const data = ref({ conversations: {}, messages: {}, agent_operations: {} })
const agentOps = ref([])
const statusChart = ref(null)
const senderChart = ref(null)

onMounted(loadData)

async function loadData() {
  try {
    const resp = await api.get('/dashboard/performance', { params: { days: days.value } })
    data.value = resp.data
    agentOps.value = Object.entries(resp.data.agent_operations || {}).map(([type, stats]) => ({
      type, ...stats,
    }))
    await nextTick()
    renderCharts()
  } catch (e) { /* ignore */ }
}

function renderCharts() {
  const d = data.value

  // 会话状态饼图
  if (statusChart.value) {
    const c = echarts.init(statusChart.value)
    const byStatus = d.conversations?.by_status || {}
    c.setOption({
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie', radius: ['40%', '70%'],
        data: Object.entries(byStatus).map(([k, v]) => ({
          name: { open: '进行中', pending: '待接入', resolved: '已结束', snoozed: '暂缓' }[k] || k,
          value: v,
        })),
        emphasis: { itemStyle: { shadowBlur: 10 } },
      }],
    })
  }

  // 消息发送者柱状图
  if (senderChart.value) {
    const c = echarts.init(senderChart.value)
    const bySender = d.messages?.by_sender_type || {}
    c.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: Object.keys(bySender).map(s => ({ contact: '客户', user: '人工客服', ai: 'AI回复', system: '系统' }[s] || s)) },
      yAxis: { type: 'value' },
      series: [{
        type: 'bar', data: Object.values(bySender),
        itemStyle: { color: '#409EFF', borderRadius: [4, 4, 0, 0] },
      }],
    })
  }
}
</script>

<style scoped>
.dashboard-page { padding: 16px; overflow-y: auto; height: 100%; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h3 { margin: 0; }
.stat-card { text-align: center; padding: 12px 0; }
.stat-value { font-size: 32px; font-weight: 700; color: #333; }
.stat-label { font-size: 13px; color: #999; margin-top: 4px; }
.stat-card.ai .stat-value { color: #67c23a; }
</style>
