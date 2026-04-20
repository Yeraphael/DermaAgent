<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import PanelCard from '@/components/PanelCard.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { auditDoctor, getAdminWorkspace, toggleDoctorService } from '@/data/controlCenter'

type Workspace = Awaited<ReturnType<typeof getAdminWorkspace>>

const workspace = ref<Workspace | null>(null)
const query = ref('')

const doctors = computed(() => {
  if (!workspace.value) return []
  const keyword = query.value.trim().toLowerCase()
  return workspace.value.doctors.filter((item) => !keyword || item.doctor_name.toLowerCase().includes(keyword) || item.hospital_name.toLowerCase().includes(keyword))
})

async function loadWorkspace() {
  workspace.value = await getAdminWorkspace()
}

async function handleAudit(doctorId: number, status: 'APPROVED' | 'PENDING' | 'REJECTED') {
  await auditDoctor(doctorId, status)
  await loadWorkspace()
  ElMessage.success('医生审核状态已更新')
}

async function handleToggleService(doctorId: number) {
  await toggleDoctorService(doctorId)
  await loadWorkspace()
  ElMessage.success('医生服务状态已更新')
}

onMounted(loadWorkspace)
</script>

<template>
  <PanelCard title="医生管理" subtitle="审核状态、服务状态和擅长方向被压缩到更精致的卡片式管理列表中。">
    <div class="form-field">
      <label>搜索医生</label>
      <input v-model="query" class="ghost-input" placeholder="姓名、医院、科室" />
    </div>

    <div class="list-panel" style="margin-top: 18px;">
      <article v-for="item in doctors" :key="item.doctor_id" class="list-row">
        <div class="list-row__head">
          <div class="avatar-row">
            <img :src="item.avatar" :alt="item.doctor_name" />
            <div>
              <strong>{{ item.doctor_name }}</strong>
              <span>{{ item.hospital_name }} · {{ item.department }} · {{ item.title_name }}</span>
            </div>
          </div>
          <div class="action-row">
            <StatusBadge :label="item.audit_status" tone="violet" />
            <StatusBadge :label="item.service_status === 1 ? '服务中' : '已暂停'" :tone="item.service_status === 1 ? 'mint' : 'slate'" />
          </div>
        </div>
        <p class="list-row__summary">擅长方向：{{ item.focus }} · 回复率 {{ item.response_rate }}</p>
        <div class="action-row" style="margin-top: 14px;">
          <button type="button" class="soft-button" @click="handleAudit(item.doctor_id, 'APPROVED')">通过</button>
          <button type="button" class="ghost-button" @click="handleAudit(item.doctor_id, 'PENDING')">待补充</button>
          <button type="button" class="ghost-button" @click="handleAudit(item.doctor_id, 'REJECTED')">驳回</button>
          <button type="button" class="primary-button" @click="handleToggleService(item.doctor_id)">
            {{ item.service_status === 1 ? '暂停服务' : '恢复服务' }}
          </button>
        </div>
      </article>
    </div>
  </PanelCard>
</template>
