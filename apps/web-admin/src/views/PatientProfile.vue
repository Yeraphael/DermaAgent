<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { client } from '@/api/client'

const route = useRoute()
const router = useRouter()
const patientId = Number(route.params.id)
const data = ref<any>(null)

async function fetchPatient() {
  try {
    const response = await client.get(`/doctor/patients/${patientId}`)
    data.value = response.data
  } catch (error) {
    ElMessage.error((error as Error).message)
  }
}

onMounted(fetchPatient)
</script>

<template>
  <div class="page-shell">
    <div class="glass-panel" style="padding: 24px;">
      <div class="section-head">
        <div>
          <h1 class="section-title">患者档案</h1>
          <p class="section-subtitle">汇总患者基础资料、健康档案和近期问诊历史。</p>
        </div>
        <el-button plain @click="router.push('/doctor')">返回工作台</el-button>
      </div>

      <div v-if="data" style="display: grid; grid-template-columns: 0.9fr 1.1fr; gap: 18px;">
        <el-card shadow="never">
          <template #header><strong>基础信息</strong></template>
          <div style="display: grid; gap: 10px;">
            <div><strong>姓名：</strong>{{ data.patient.profile.real_name }}</div>
            <div><strong>账号：</strong>{{ data.patient.account.username }}</div>
            <div><strong>年龄：</strong>{{ data.patient.profile.age }}</div>
            <div><strong>城市：</strong>{{ data.patient.profile.city }}</div>
            <div><strong>职业：</strong>{{ data.patient.profile.occupation }}</div>
            <div><strong>紧急联系人：</strong>{{ data.patient.profile.emergency_contact }} / {{ data.patient.profile.emergency_phone }}</div>
          </div>
        </el-card>

        <el-card shadow="never">
          <template #header><strong>健康档案</strong></template>
          <div style="display: grid; gap: 10px;">
            <div><strong>肤质：</strong>{{ data.patient.health_profile.skin_type || '未填写' }}</div>
            <div><strong>敏感程度：</strong>{{ data.patient.health_profile.skin_sensitivity || '未填写' }}</div>
            <div><strong>睡眠：</strong>{{ data.patient.health_profile.sleep_pattern || '未填写' }}</div>
            <div><strong>饮食偏好：</strong>{{ data.patient.health_profile.diet_preference || '未填写' }}</div>
            <div><strong>过敏史：</strong>{{ data.patient.health_profile.allergy_history || '未填写' }}</div>
            <div><strong>既往史：</strong>{{ data.patient.health_profile.past_medical_history || '未填写' }}</div>
            <div><strong>用药史：</strong>{{ data.patient.health_profile.medication_history || '未填写' }}</div>
            <div><strong>备注：</strong>{{ data.patient.health_profile.special_notes || '未填写' }}</div>
          </div>
        </el-card>
      </div>

      <div style="height: 18px;" />

      <el-card shadow="never" v-if="data">
        <template #header><strong>近期问诊记录</strong></template>
        <el-table :data="data.recent_consultations">
          <el-table-column prop="case_no" label="病例号" min-width="160" />
          <el-table-column prop="summary_title" label="摘要" min-width="180" />
          <el-table-column prop="risk_level" label="风险" width="120" />
          <el-table-column prop="status" label="状态" width="140" />
          <el-table-column prop="submitted_at" label="提交时间" width="180" />
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button size="small" @click="router.push(`/doctor/consultations/${row.case_id}`)">查看</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </div>
</template>
