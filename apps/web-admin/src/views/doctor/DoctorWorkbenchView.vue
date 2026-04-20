<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import MetricCard from '@/components/MetricCard.vue'
import PanelCard from '@/components/PanelCard.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import TrendChart from '@/components/TrendChart.vue'
import { getConsultationStatusLabel, getDoctorWorkspace, getRiskLabel } from '@/data/controlCenter'

const router = useRouter()
const workspace = ref<Awaited<ReturnType<typeof getDoctorWorkspace>> | null>(null)

function toneFromRisk(risk: 'LOW' | 'MEDIUM' | 'HIGH') {
  return risk === 'HIGH' ? 'rose' : risk === 'MEDIUM' ? 'amber' : 'mint'
}

function toneFromStatus(status: string) {
  if (status === 'WAIT_DOCTOR') return 'amber'
  if (status === 'DOCTOR_REPLIED') return 'mint'
  if (status === 'AI_DONE') return 'blue'
  return 'slate'
}

async function loadWorkspace() {
  workspace.value = await getDoctorWorkspace()
}

onMounted(loadWorkspace)
</script>

<template>
  <template v-if="workspace">
    <section class="metric-grid">
      <MetricCard
        v-for="metric in workspace.metrics"
        :key="metric.label"
        :label="metric.label"
        :value="metric.value"
        :change="metric.change"
        :accent="metric.accent"
      />
    </section>

    <section class="split-grid">
      <PanelCard
        title="优先处理队列"
        subtitle="把高风险预警、待回复问诊和 AI 已完成案例集中到同一视图。"
      >
        <div class="list-panel">
          <article
            v-for="item in workspace.queue.slice(0, 4)"
            :key="item.case_id"
            class="list-row"
            @click="router.push(`/doctor/consultations/${item.case_id}`)"
          >
            <div class="list-row__head">
              <div class="avatar-row">
                <img :src="item.patient.avatar" :alt="item.patient.name" />
                <div>
                  <strong>{{ item.patient.name }}</strong>
                  <span>{{ item.patient.gender }} · {{ item.patient.age }} 岁 · {{ item.submitted_at }}</span>
                </div>
              </div>
              <StatusBadge :label="getConsultationStatusLabel(item.status)" :tone="toneFromStatus(item.status)" />
            </div>
            <p class="list-row__summary">{{ item.summary_title }}</p>
            <div class="action-row" style="margin-top: 12px;">
              <StatusBadge :label="getRiskLabel(item.risk_level)" :tone="toneFromRisk(item.risk_level)" />
              <StatusBadge :label="item.ai_result.condition_guess" tone="blue" />
            </div>
          </article>
        </div>
      </PanelCard>

      <PanelCard
        title="今日焦点病例"
        subtitle="重点展示 AI 观察结论、风险等级和医生下一步动作建议。"
      >
        <div class="detail-card">
          <div class="detail-row">
            <div>
              <div class="tiny-label">当前病例</div>
              <p class="detail-title">{{ workspace.focusCase.case_no }}</p>
            </div>
            <StatusBadge :label="getRiskLabel(workspace.focusCase.risk_level)" :tone="toneFromRisk(workspace.focusCase.risk_level)" />
          </div>
          <p class="detail-copy">{{ workspace.focusCase.ai_result.image_observation }}</p>
        </div>

        <div class="progress-list" style="margin-top: 18px;">
          <div
            v-for="item in workspace.focusCase.ai_result.possible_directions"
            :key="item.label"
            class="progress-item"
          >
            <span>{{ item.label }}</span>
            <div class="progress-track"><span :style="{ width: `${item.value}%` }" /></div>
            <strong>{{ item.value }}%</strong>
          </div>
        </div>

        <div class="action-row" style="margin-top: 20px;">
          <button type="button" class="primary-button" @click="router.push(`/doctor/consultations/${workspace.focusCase.case_id}`)">进入病例详情</button>
          <button type="button" class="ghost-button" @click="router.push('/doctor/patients')">查看患者档案</button>
        </div>
      </PanelCard>
    </section>

    <section class="split-grid">
      <PanelCard
        title="医生效率趋势"
        subtitle="AI 辅助结果与高风险问诊量同图展示，强调专业效率感而不是传统后台风。"
      >
        <TrendChart :points="workspace.trend" />
      </PanelCard>

      <PanelCard
        title="高风险提醒"
        subtitle="将需要优先线下就医建议或扩散观察的案例单独收口。"
      >
        <div class="log-list">
          <article v-for="item in workspace.alerts" :key="item.case_id" class="log-item">
            <strong>{{ item.summary_title }}</strong>
            <p>{{ item.ai_result.alert }}</p>
            <div class="action-row" style="margin-top: 12px;">
              <StatusBadge :label="item.patient.name" tone="slate" />
              <StatusBadge :label="item.case_no" tone="blue" />
            </div>
          </article>
        </div>
      </PanelCard>
    </section>
  </template>
</template>
