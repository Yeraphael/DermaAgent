<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import PanelCard from '@/components/PanelCard.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { getAdminWorkspace, updateUserStatus } from '@/data/controlCenter'

type Workspace = Awaited<ReturnType<typeof getAdminWorkspace>>

const workspace = ref<Workspace | null>(null)
const query = ref('')
const statusFilter = ref<'ALL' | '1' | '0'>('ALL')

const users = computed(() => {
  if (!workspace.value) return []
  const keyword = query.value.trim().toLowerCase()
  return workspace.value.users.filter((item) => {
    const matchesStatus = statusFilter.value === 'ALL' || String(item.status) === statusFilter.value
    const matchesKeyword = !keyword || item.real_name.toLowerCase().includes(keyword) || item.username.toLowerCase().includes(keyword)
    return matchesStatus && matchesKeyword
  })
})

async function loadWorkspace() {
  workspace.value = await getAdminWorkspace()
}

async function toggleStatus(accountId: number, status: 0 | 1) {
  await updateUserStatus(accountId, status)
  await loadWorkspace()
  ElMessage.success(status === 1 ? '用户已启用' : '用户已停用')
}

onMounted(loadWorkspace)
</script>

<template>
  <PanelCard title="用户管理" subtitle="用户列表被重构成更轻盈的管理视图，状态、联系方式和行为偏好保持清晰层级。">
    <div class="split-grid">
      <div class="form-field">
        <label>搜索用户</label>
        <input v-model="query" class="ghost-input" placeholder="姓名、账号" />
      </div>
      <div class="form-field">
        <label>状态筛选</label>
        <div class="segment">
          <button type="button" class="segment-button" :class="{ 'is-active': statusFilter === 'ALL' }" @click="statusFilter = 'ALL'">全部</button>
          <button type="button" class="segment-button" :class="{ 'is-active': statusFilter === '1' }" @click="statusFilter = '1'">正常</button>
          <button type="button" class="segment-button" :class="{ 'is-active': statusFilter === '0' }" @click="statusFilter = '0'">停用</button>
        </div>
      </div>
    </div>

    <div class="table-shell" style="margin-top: 18px;">
      <div class="table-head" style="--columns: 1.2fr 1fr 1fr 1fr 1.2fr 1fr;">
        <span>用户</span>
        <span>联系方式</span>
        <span>城市</span>
        <span>最新问诊</span>
        <span>偏好</span>
        <span>操作</span>
      </div>
      <div
        v-for="item in users"
        :key="item.account_id"
        class="table-row"
        style="--columns: 1.2fr 1fr 1fr 1fr 1.2fr 1fr;"
      >
        <div>
          <strong>{{ item.real_name }}</strong>
          <span class="table-cell__sub">@{{ item.username }}</span>
        </div>
        <div>{{ item.phone }}</div>
        <div>{{ item.city }}</div>
        <div>{{ item.latest_case }}</div>
        <div>
          <StatusBadge :label="item.tag" tone="violet" />
          <span class="table-cell__sub">{{ item.risk_preference }}</span>
        </div>
        <div class="action-row">
          <button type="button" class="soft-button" @click="toggleStatus(item.account_id, 1)">启用</button>
          <button type="button" class="ghost-button" @click="toggleStatus(item.account_id, 0)">停用</button>
        </div>
      </div>
    </div>
  </PanelCard>
</template>
