<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import RiskBadge from '../components/RiskBadge.vue'
import { getPortalConsultations, getPortalNotifications, getPortalRiskLabel, getPortalStatusLabel } from '../shared/portal'

const router = useRouter()
const filter = ref<'ALL' | 'AI' | 'DOCTOR' | 'SYSTEM'>('ALL')

const timeline = computed(() => {
  const consultations = getPortalConsultations().map((item) => ({
    id: item.caseId,
    kind: item.status === 'DOCTOR_REPLIED' ? 'DOCTOR' : 'AI',
    title: item.title,
    summary: item.ai.observation,
    meta: `${item.caseNo} · ${getPortalStatusLabel(item.status)} · ${getPortalRiskLabel(item.riskLevel)}`,
    caseId: item.caseId,
  }))

  const notifications = getPortalNotifications().map((item) => ({
    id: item.id,
    kind: item.category,
    title: item.title,
    summary: item.summary,
    meta: item.time,
    caseId: item.linkedCaseId,
  }))

  return [...consultations, ...notifications].filter((item) => filter.value === 'ALL' || item.kind === filter.value)
})

function tone(kind: string) {
  if (kind === 'DOCTOR') return 'mint'
  if (kind === 'SYSTEM') return 'violet'
  return 'blue'
}
</script>

<template>
  <section class="page-stack">
    <article class="surface-card">
      <div class="section-head">
        <div>
          <p class="section-eyebrow">历史记录与通知</p>
          <h1 class="section-title">所有关键节点都收口在一个时间线里</h1>
          <p class="section-subtitle">AI 分析完成、医生回复、系统通知与历史病例统一用同一套卡片层级展示。</p>
        </div>
      </div>
      <div class="segment">
        <button type="button" :class="{ 'is-active': filter === 'ALL' }" @click="filter = 'ALL'">全部</button>
        <button type="button" :class="{ 'is-active': filter === 'AI' }" @click="filter = 'AI'">AI 分析</button>
        <button type="button" :class="{ 'is-active': filter === 'DOCTOR' }" @click="filter = 'DOCTOR'">医生回复</button>
        <button type="button" :class="{ 'is-active': filter === 'SYSTEM' }" @click="filter = 'SYSTEM'">系统通知</button>
      </div>
    </article>

    <div class="timeline-list">
      <article
        v-for="item in timeline"
        :key="`${item.kind}-${item.id}`"
        class="timeline-item"
        @click="item.caseId ? router.push(`/analysis/${item.caseId}`) : undefined"
      >
        <strong>{{ item.title }}</strong>
        <p>{{ item.summary }}</p>
        <div class="action-row" style="margin-top: 12px;">
          <RiskBadge :label="item.kind" :tone="tone(item.kind)" />
        </div>
        <span>{{ item.meta }}</span>
      </article>
    </div>
  </section>
</template>
