<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { client } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const loading = ref(false)
const dashboard = ref<any>(null)
const list = ref<any[]>([])
const filters = reactive({
  status: '',
  keyword: '',
})

async function fetchDashboard() {
  const response = await client.get('/doctor/dashboard')
  dashboard.value = response.data
}

async function fetchList() {
  loading.value = true
  try {
    const response = await client.get('/doctor/consultations', {
      params: {
        status: filters.status || undefined,
        keyword: filters.keyword || undefined,
        page: 1,
        page_size: 50,
      },
    })
    list.value = response.data.list
  } finally {
    loading.value = false
  }
}

function openCase(row: any) {
  router.push(`/doctor/consultations/${row.case_id}`)
}

function openPatient(row: any) {
  router.push(`/doctor/patients/${row.patient.user.account_id}`)
}

async function init() {
  try {
    await Promise.all([fetchDashboard(), fetchList()])
  } catch (error) {
    ElMessage.error((error as Error).message)
  }
}

function logout() {
  auth.logout()
  router.replace('/login')
}

onMounted(init)
</script>

<template>
  <div class="page-shell">
    <div class="glass-panel" style="padding: 28px 28px 22px;">
      <div class="section-head">
        <div>
          <h1 class="section-title">医生工作台</h1>
          <p class="section-subtitle">聚合待处理问诊、AI 结果参考、患者信息和回复闭环。</p>
        </div>
        <div style="display: flex; align-items: center; gap: 12px;">
          <el-tag v-if="dashboard?.doctor" type="success" size="large">{{ dashboard.doctor.doctor_name }} · {{ dashboard.doctor.title_name }}</el-tag>
          <el-button plain @click="logout">退出</el-button>
        </div>
      </div>

      <div v-if="dashboard" class="stat-grid">
        <div class="stat-card">
          <span class="stat-label">待复核问诊</span>
          <strong>{{ dashboard.stats.pending_total }}</strong>
        </div>
        <div class="stat-card">
          <span class="stat-label">已回复病例</span>
          <strong>{{ dashboard.stats.replied_total }}</strong>
        </div>
        <div class="stat-card">
          <span class="stat-label">已结案问诊</span>
          <strong>{{ dashboard.stats.closed_total }}</strong>
        </div>
        <div class="stat-card">
          <span class="stat-label">高风险提醒</span>
          <strong>{{ dashboard.stats.high_risk_total }}</strong>
        </div>
      </div>
    </div>

    <div style="height: 18px;" />

    <div class="glass-panel" style="padding: 24px;">
      <div class="section-head">
        <div>
          <h2 class="section-title">问诊列表</h2>
          <p class="section-subtitle">按状态筛选问诊单，进入详情页查看 AI 分析与患者档案。</p>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 220px 1fr 120px; gap: 14px; margin-bottom: 18px;">
        <el-select v-model="filters.status" clearable placeholder="筛选状态">
          <el-option label="待医生处理" value="WAIT_DOCTOR" />
          <el-option label="已回复" value="DOCTOR_REPLIED" />
          <el-option label="已关闭" value="CLOSED" />
          <el-option label="AI 已完成" value="AI_DONE" />
        </el-select>
        <el-input v-model="filters.keyword" placeholder="搜索病例号、摘要或主诉" />
        <el-button class="accent-button" type="primary" @click="fetchList">刷新</el-button>
      </div>

      <el-table :data="list" v-loading="loading" height="560">
        <el-table-column prop="case_no" label="病例号" min-width="160" />
        <el-table-column prop="summary_title" label="问诊摘要" min-width="180" />
        <el-table-column label="患者" min-width="140">
          <template #default="{ row }">
            {{ row.patient?.profile?.real_name || row.patient?.user?.username }}
          </template>
        </el-table-column>
        <el-table-column label="风险" width="110">
          <template #default="{ row }">
            <el-tag :type="row.risk_level === 'HIGH' ? 'danger' : row.risk_level === 'MEDIUM' ? 'warning' : 'success'">
              {{ row.risk_level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="150">
          <template #default="{ row }">
            <el-tag effect="dark" :type="row.status === 'WAIT_DOCTOR' ? 'warning' : row.status === 'DOCTOR_REPLIED' ? 'success' : 'info'">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="AI 风险" width="120">
          <template #default="{ row }">
            {{ row.ai_result?.risk_level || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="submitted_at" label="提交时间" width="180" />
        <el-table-column label="操作" min-width="180" fixed="right">
          <template #default="{ row }">
            <div style="display: flex; gap: 8px;">
              <el-button size="small" @click="openCase(row)">查看详情</el-button>
              <el-button size="small" type="success" plain @click="openPatient(row)">患者档案</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>
