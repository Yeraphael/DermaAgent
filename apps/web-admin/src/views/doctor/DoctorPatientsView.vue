<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import EmptyState from '@/components/EmptyState.vue'
import PanelCard from '@/components/PanelCard.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { getConsultationStatusLabel, getDoctorPatients, getRiskLabel } from '@/data/controlCenter'

type DoctorPatient = Awaited<ReturnType<typeof getDoctorPatients>>[number]

const patients = ref<DoctorPatient[]>([])
const query = ref('')
const selectedPatientId = ref<number | null>(null)

const filteredPatients = computed(() => {
  const keyword = query.value.trim().toLowerCase()
  return patients.value.filter((item) => {
    return !keyword || item.name.toLowerCase().includes(keyword) || item.tags.join('').toLowerCase().includes(keyword)
  })
})

const selectedPatient = computed(() => {
  return filteredPatients.value.find((item) => item.patient_id === selectedPatientId.value) || filteredPatients.value[0] || null
})

async function loadPatients() {
  patients.value = await getDoctorPatients()
  selectedPatientId.value = patients.value[0]?.patient_id || null
}

onMounted(loadPatients)
</script>

<template>
  <section class="split-grid" style="grid-template-columns: 340px minmax(0, 1fr);">
    <PanelCard title="患者管理" subtitle="历史病例与健康档案聚合展示，帮助医生建立连续性的判断。">
      <div class="form-field">
        <label>搜索患者</label>
        <input v-model="query" class="ghost-input" placeholder="姓名、标签、健康关注点" />
      </div>

      <div class="list-panel" style="margin-top: 18px;">
        <article
          v-for="item in filteredPatients"
          :key="item.patient_id"
          class="list-row"
          :class="{ 'is-active': selectedPatient?.patient_id === item.patient_id }"
          @click="selectedPatientId = item.patient_id"
        >
          <div class="avatar-row">
            <img :src="item.avatar" :alt="item.name" />
            <div>
              <strong>{{ item.name }}</strong>
              <span>{{ item.gender }} · {{ item.age }} 岁 · {{ item.city }}</span>
            </div>
          </div>
          <div class="pill-stack" style="margin-top: 12px;">
            <StatusBadge v-for="tag in item.tags.slice(0, 2)" :key="tag" :label="tag" tone="blue" />
          </div>
        </article>
      </div>
    </PanelCard>

    <PanelCard v-if="selectedPatient" title="患者健康档案" subtitle="病例历史、过敏信息、生活习惯与皮肤类型保持同一视觉层级。">
      <div class="split-grid">
        <article class="detail-card">
          <div class="avatar-row">
            <img :src="selectedPatient.avatar" :alt="selectedPatient.name" />
            <div>
              <strong>{{ selectedPatient.name }}</strong>
              <span>{{ selectedPatient.gender }} · {{ selectedPatient.age }} 岁 · {{ selectedPatient.city }}</span>
            </div>
          </div>
          <div class="action-row" style="margin-top: 14px;">
            <StatusBadge :label="`健康评分 ${selectedPatient.health_score}`" tone="mint" />
            <StatusBadge :label="selectedPatient.skin_type" tone="violet" />
          </div>
        </article>

        <article class="detail-card">
          <div class="tiny-label">生活与护理信息</div>
          <div class="key-value" style="margin-top: 10px;">
            <div class="key-value__row">
              <span>过敏史</span>
              <strong>{{ selectedPatient.allergies.join('、') }}</strong>
            </div>
            <div class="key-value__row">
              <span>长期用药</span>
              <strong>{{ selectedPatient.medications.join('、') }}</strong>
            </div>
            <div class="key-value__row">
              <span>生活习惯</span>
              <strong>{{ selectedPatient.habits.join('、') }}</strong>
            </div>
          </div>
        </article>
      </div>

      <div class="detail-card" style="margin-top: 18px;">
        <div class="tiny-label">历史病例</div>
        <div class="list-panel" style="margin-top: 14px;">
          <article v-for="item in selectedPatient.recentCases" :key="item.case_id" class="list-row">
            <div class="list-row__head">
              <div>
                <strong>{{ item.summary_title }}</strong>
                <p class="list-row__summary">{{ item.case_no }} · {{ item.submitted_at }}</p>
              </div>
              <StatusBadge :label="getConsultationStatusLabel(item.status)" tone="blue" />
            </div>
            <div class="action-row" style="margin-top: 12px;">
              <StatusBadge :label="getRiskLabel(item.risk_level)" tone="amber" />
              <StatusBadge :label="item.ai_result.condition_guess" tone="slate" />
            </div>
          </article>
        </div>
      </div>
    </PanelCard>

    <PanelCard v-else title="暂无患者信息" subtitle="当前筛选下没有匹配患者。">
      <EmptyState title="没有查到患者" copy="可以清空搜索词，或者回到问诊管理页从病例快速进入患者档案。" />
    </PanelCard>
  </section>
</template>
