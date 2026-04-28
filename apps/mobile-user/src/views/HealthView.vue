<script setup lang="ts">
import { computed } from 'vue'

import RiskBadge from '../components/RiskBadge.vue'
import { getPortalConsultations, getPortalProfile, getPortalRiskLabel } from '../shared/portal'

const profile = computed(() => getPortalProfile())
const cases = computed(() => getPortalConsultations().slice(0, 3))

function riskTone(risk: 'LOW' | 'MEDIUM' | 'HIGH') {
  return risk === 'HIGH' ? 'rose' : risk === 'MEDIUM' ? 'amber' : 'mint'
}
</script>

<template>
  <section class="page-stack">
    <article class="surface-card">
      <div class="section-head">
        <div>
          <p class="section-eyebrow">健康档案</p>
          <h1 class="section-title">你的皮肤健康档案</h1>
          <p class="section-subtitle">把症状、风险等级、医生回复和护理建议沉淀成可持续追踪的健康档案。</p>
        </div>
      </div>
      <div class="grid-3">
        <article class="metric-card">
          <span>皮肤类型</span>
          <strong>{{ profile.healthArchive.skinType }}</strong>
        </article>
        <article class="metric-card">
          <span>最近 30 天</span>
          <strong>3 次问诊</strong>
        </article>
        <article class="metric-card">
          <span>护理节奏</span>
          <strong>已建立</strong>
        </article>
      </div>
    </article>

    <div class="grid-2">
      <article class="surface-card">
        <div class="section-head">
          <div>
            <p class="section-eyebrow">风险趋势</p>
            <h2 class="card-title">最近记录</h2>
          </div>
        </div>
        <div class="timeline-list">
          <article v-for="item in profile.healthArchive.riskTrend" :key="item" class="timeline-item">
            <strong>趋势记录</strong>
            <p>{{ item }}</p>
          </article>
        </div>
      </article>

      <article class="surface-card">
        <div class="section-head">
          <div>
            <p class="section-eyebrow">最近病例</p>
            <h2 class="card-title">档案摘要</h2>
          </div>
        </div>
        <div class="timeline-list">
          <article v-for="item in cases" :key="item.caseId" class="timeline-item">
            <strong>{{ item.title }}</strong>
            <p>{{ item.description }}</p>
            <div class="action-row" style="margin-top: 12px;">
              <RiskBadge :label="getPortalRiskLabel(item.riskLevel)" :tone="riskTone(item.riskLevel)" />
            </div>
          </article>
        </div>
      </article>
    </div>
  </section>
</template>
