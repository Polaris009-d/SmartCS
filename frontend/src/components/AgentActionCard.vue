<template>
  <div :class="['agent-action-card', data?.status === 'success' ? 'success' : 'failed']">
    <div class="card-header">
      <el-icon v-if="data?.status === 'success'" color="#67c23a"><CircleCheck /></el-icon>
      <el-icon v-else color="#f56c6c"><CircleClose /></el-icon>
      <span class="card-title">{{ actionLabel }}</span>
    </div>
    <div class="card-body">{{ data?.message }}</div>

    <!-- 可选订单列表 -->
    <div v-if="data?.orders && data.orders.length > 0" class="refund-order-list">
      <div v-for="o in data.orders" :key="o.order_no"
        :class="['refund-order-item', { recommended: o.order_no === data?.last_order_no }]">
        <div class="order-info">
          <strong>{{ o.order_no }}</strong>
          <el-tag v-if="o.order_no === data?.last_order_no" type="success" size="small">上次查询</el-tag>
          <span class="order-product">{{ o.product_name }}</span>
          <span class="order-amount">¥{{ o.total_amount }}</span>
          <el-tag :type="orderStatusTag(o.status)" size="small">{{ orderStatusLabel(o.status) }}</el-tag>
        </div>
        <el-button v-if="isRefund" size="small" type="danger" @click="$emit('refundOrder', o.order_no)">申请退款</el-button>
        <el-button v-else-if="isOrder" size="small" type="primary" @click="$emit('queryOrder', o.order_no)">查看</el-button>
        <el-button v-else size="small" type="primary" @click="$emit('queryLogistics', o.order_no)">查物流</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ data: Object })
defineEmits(['refundOrder', 'queryOrder', 'queryLogistics'])

const isRefund = computed(() => (props.data?.action || '').startsWith('refund'))
const isOrder = computed(() => (props.data?.action || '').startsWith('order'))

const actionLabel = computed(() => {
  const a = props.data?.action || ''
  if (a.includes('order')) return '订单查询'
  if (a.includes('logistics')) return '物流查询'
  if (a.includes('refund')) return '退款处理'
  return 'Agent 操作'
})

function orderStatusTag(s) {
  return { pending: 'info', paid: '', shipped: 'warning', delivered: 'success', cancelled: 'info', refunding: 'danger' }[s] || ''
}
function orderStatusLabel(s) {
  return { pending: '待付', paid: '已付', shipped: '运输中', delivered: '已签收', cancelled: '已取消', refunding: '退款中' }[s] || s
}
</script>

<style scoped>
.agent-action-card { border-radius: 8px; padding: 12px; margin: 4px 0; }
.agent-action-card.success { background: #f0f9eb; border: 1px solid #e1f3d8; }
.agent-action-card.failed { background: #fef0f0; border: 1px solid #fde2e2; }
.card-header { display: flex; align-items: center; gap: 6px; font-weight: 600; margin-bottom: 6px; }
.card-body { font-size: 13px; margin-bottom: 8px; }
.refund-order-list { display: flex; flex-direction: column; gap: 8px; }
.refund-order-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 12px; background: #fff; border: 1px solid #e6e6e6; border-radius: 6px;
}
.order-info { display: flex; align-items: center; gap: 10px; font-size: 13px; }
.order-product { color: #666; max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.order-amount { font-weight: 700; color: #f56c6c; }
.refund-order-item.recommended { border-color: #67c23a; background: #f0f9eb; }
</style>
