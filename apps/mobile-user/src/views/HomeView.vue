<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import RiskBadge from '../components/RiskBadge.vue'
import { getPortalDashboard, getPortalRiskLabel, getPortalStatusLabel } from '../shared/portal'

const router = useRouter()
const dashboard = computed(() => getPortalDashboard())

function riskTone(risk: 'LOW' | 'MEDIUM' | 'HIGH') {
  return risk === 'HIGH' ? 'rose' : risk === 'MEDIUM' ? 'amber' : 'mint'
}

function statusTone(status: string) {
  if (status === 'DOCTOR_REPLIED') return 'mint'
  if (status === 'WAIT_DOCTOR') return 'amber'
  if (status === 'AI_DONE') return 'blue'
  return 'slate'
}
</script>

<template>
  <section class="page-stack">
    <div class="hero-grid">
      <article class="surface-card hero-card">
        <div>
          <p class="section-eyebrow">智能问诊入口</p>
          <h1 class="section-title">你好，{{ dashboard.profile.real_name }}。今天也让皮肤状态更稳定一点。</h1>
          <p class="section-subtitle">
            这里是你的 AI 皮肤健康助手。上传 1-5 张皮肤图片、补充症状和时长后，
            系统会给出初步观察、风险级别、护理建议，并在需要时接入医生回复。
          </p>
        </div>

        <div class="action-row">
          <button type="button" class="primary-button" @click="router.push('/consultation')">开始问诊</button>
          <button type="button" class="ghost-button" @click="router.push('/analysis')">查看 AI 结果</button>
        </div>

        <div class="hero-card__visual" />
      </article>

      <article class="surface-card">
        <div class="section-head">
          <div>
            <p class="section-eyebrow">概览</p>
            <h2 class="card-title">当前健康状态</h2>
          </div>
        </div>
        <div class="grid-2">
          <article class="metric-card">
            <span>问诊总量</span>
            <strong>{{ dashboard.summary.consultationTotal }}</strong>
          </article>
          <article class="metric-card">
            <span>待医生回复</span>
            <strong>{{ dashboard.summary.waitingTotal }}</strong>
          </article>
          <article class="metric-card">
            <span>医生已回复</span>
            <strong>{{ dashboard.summary.doctorReplyTotal }}</strong>
          </article>
          <article class="metric-card">
            <span>未读通知</span>
            <strong>{{ dashboard.summary.unreadNotifications }}</strong>
          </article>
        </div>
      </article>
    </div>

    <div class="grid-3">
      <article v-for="item in dashboard.quickActions" :key="item.key" class="surface-card surface-card--compact">
        <p class="section-eyebrow">{{ item.description }}</p>
        <h3 class="card-title" style="font-size: 22px; margin-top: 10px;">{{ item.label }}</h3>
        <p class="card-copy">围绕肤联智诊的真实业务入口做成可运行页面，而不是静态示意图。</p>
      </article>
    </div>

    <div class="history-grid">
      <article class="surface-card">
        <div class="section-head">
          <div>
            <p class="section-eyebrow">进行中案例</p>
            <h2 class="card-title">{{ dashboard.ongoingCase.title }}</h2>
          </div>
          <RiskBadge :label="getPortalRiskLabel(dashboard.ongoingCase.riskLevel)" :tone="riskTone(dashboard.ongoingCase.riskLevel)" />
        </div>
        <p class="card-copy">{{ dashboard.ongoingCase.ai.observation }}</p>
        <div class="action-row" style="margin-top: 14px;">
          <RiskBadge :label="getPortalStatusLabel(dashboard.ongoingCase.status)" :tone="statusTone(dashboard.ongoingCase.status)" />
          <RiskBadge :label="dashboard.ongoingCase.caseNo" tone="slate" />
        </div>
        <button type="button" class="primary-button" style="margin-top: 18px;" @click="router.push(`/analysis/${dashboard.ongoingCase.caseId}`)">
          查看分析详情
        </button>
      </article>

      <article class="surface-card">
        <div class="section-head">
          <div>
            <p class="section-eyebrow">最近记录与通知</p>
            <h2 class="card-title">保持连续追踪</h2>
          </div>
        </div>
        <div class="timeline-list">
          <article v-for="item in dashboard.notifications" :key="item.id" class="notification-item">
            <strong>{{ item.title }}</strong>
            <p>{{ item.summary }}</p>
            <span>{{ item.time }}</span>
          </article>
        </div>
      </article>
    </div>

    <article class="surface-card">
      <div class="section-head">
        <div>
          <p class="section-eyebrow">最近问诊记录</p>
          <h2 class="card-title">历史案例</h2>
        </div>
        <button type="button" class="ghost-button" @click="router.push('/history')">全部记录</button>
      </div>
      <div class="grid-3">
        <article
          v-for="item in dashboard.recentCases"
          :key="item.caseId"
          class="list-card"
          @click="router.push(`/analysis/${item.caseId}`)"
        >
          <p class="list-card__title">{{ item.title }}</p>
          <p class="list-card__copy">{{ item.description }}</p>
          <div class="action-row" style="margin-top: 14px;">
            <RiskBadge :label="getPortalRiskLabel(item.riskLevel)" :tone="riskTone(item.riskLevel)" />
            <RiskBadge :label="getPortalStatusLabel(item.status)" :tone="statusTone(item.status)" />
          </div>
        </article>
      </div>
    </article>
  </section>
</template>
