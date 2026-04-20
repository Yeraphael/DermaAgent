<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import DirectionBars from '../components/DirectionBars.vue'
import RiskBadge from '../components/RiskBadge.vue'
import {
  buildVisualStyle,
  getPortalConsultation,
  getPortalConsultations,
  getPortalNotifications,
  getPortalRiskLabel,
  getPortalStatusLabel,
} from '../shared/portal'

const props = defineProps<{
  caseId?: string
}>()

const router = useRouter()
const detail = computed(() => {
  const id = Number(props.caseId)
  return (id ? getPortalConsultation(id) : null) || getPortalConsultations()[0]
})

const sideCases = computed(() => getPortalConsultations().slice(0, 3))
const notifications = computed(() => getPortalNotifications().slice(0, 3))

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
  <section v-if="detail" class="analysis-layout">
    <article class="surface-card">
      <div class="section-head">
        <div>
          <p class="section-eyebrow">病例摘要</p>
          <h1 class="section-title">{{ detail.title }}</h1>
          <p class="section-subtitle">{{ detail.caseNo }} · {{ detail.submittedAt }}</p>
        </div>
      </div>
      <div class="action-row">
        <RiskBadge :label="getPortalRiskLabel(detail.riskLevel)" :tone="riskTone(detail.riskLevel)" />
        <RiskBadge :label="getPortalStatusLabel(detail.status)" :tone="statusTone(detail.status)" />
      </div>
      <div class="surface-card surface-card--compact" style="margin-top: 18px;">
        <p class="section-eyebrow">症状信息</p>
        <p class="card-copy">{{ detail.description }}</p>
        <div class="action-row" style="margin-top: 14px;">
          <RiskBadge :label="`发病时长 · ${detail.onsetDuration}`" tone="slate" />
          <RiskBadge :label="`瘙痒 ${detail.itchLevel}`" tone="violet" />
          <RiskBadge :label="`疼痛 ${detail.painLevel}`" tone="rose" />
        </div>
      </div>
      <div class="visual-strip" style="margin-top: 18px;">
        <div v-for="item in detail.visuals.slice(0, 3)" :key="item" class="visual-tile" :style="buildVisualStyle(item)" />
      </div>
      <div class="surface-card surface-card--compact" style="margin-top: 18px;">
        <p class="section-eyebrow">继续查看</p>
        <div class="timeline-list" style="margin-top: 12px;">
          <article
            v-for="item in sideCases"
            :key="item.caseId"
            class="timeline-item"
            @click="router.push(`/analysis/${item.caseId}`)"
          >
            <strong>{{ item.title }}</strong>
            <p>{{ item.caseNo }}</p>
          </article>
        </div>
      </div>
    </article>

    <article class="surface-card">
      <div class="section-head">
        <div>
          <p class="section-eyebrow">AI 分析结果</p>
          <h2 class="card-title">图片初步观察与风险建议</h2>
        </div>
        <RiskBadge :label="detail.ai.shouldVisit ? '建议复核' : '可先观察'" :tone="detail.ai.shouldVisit ? 'amber' : 'mint'" />
      </div>

      <div class="surface-card surface-card--compact">
        <p class="section-eyebrow">图片初步观察</p>
        <p class="card-copy">{{ detail.ai.observation }}</p>
      </div>

      <div class="surface-card surface-card--compact" style="margin-top: 18px;">
        <p class="section-eyebrow">可能相关方向</p>
        <DirectionBars :items="detail.ai.directions" />
      </div>

      <div class="surface-card surface-card--compact" style="margin-top: 18px;">
        <p class="section-eyebrow">护理建议</p>
        <div class="timeline-list" style="margin-top: 12px;">
          <article v-for="item in detail.ai.careAdvice" :key="item" class="timeline-item">
            <strong>护理建议</strong>
            <p>{{ item }}</p>
          </article>
        </div>
      </div>

      <div class="surface-card surface-card--compact" style="margin-top: 18px;">
        <p class="section-eyebrow">是否建议就医</p>
        <p class="card-copy">{{ detail.ai.riskReason }}</p>
        <div class="action-row" style="margin-top: 12px;">
          <RiskBadge :label="detail.ai.shouldVisit ? '建议线下就医' : '暂不急需就医'" :tone="detail.ai.shouldVisit ? 'rose' : 'mint'" />
        </div>
      </div>
    </article>

    <article class="surface-card">
      <div class="section-head">
        <div>
          <p class="section-eyebrow">医生回复 / 知识问答</p>
          <h2 class="card-title">沟通与科普</h2>
        </div>
      </div>

      <div v-if="detail.doctorReply" class="surface-card surface-card--compact">
        <p class="section-eyebrow">医生回复</p>
        <h3 class="card-title" style="font-size: 22px; margin-top: 8px;">{{ detail.doctorReply.doctorName }}</h3>
        <p class="section-subtitle">{{ detail.doctorReply.title }} · {{ detail.doctorReply.repliedAt }}</p>
        <p class="card-copy">{{ detail.doctorReply.content }}</p>
        <div class="timeline-list" style="margin-top: 12px;">
          <article v-for="item in detail.doctorReply.suggestion" :key="item" class="timeline-item">
            <strong>建议</strong>
            <p>{{ item }}</p>
          </article>
        </div>
      </div>

      <div class="surface-card surface-card--compact" style="margin-top: 18px;">
        <p class="section-eyebrow">知识问答</p>
        <div class="timeline-list" style="margin-top: 12px;">
          <article class="timeline-item" @click="router.push('/qa')">
            <strong>泛红和过敏有什么区别？</strong>
            <p>点击进入知识问答，获取基于护理知识库的进一步说明。</p>
          </article>
          <article class="timeline-item" @click="router.push('/qa')">
            <strong>如何判断是不是屏障受损？</strong>
            <p>系统会结合你的症状、护理史和问答上下文给出更明确的解释。</p>
          </article>
        </div>
      </div>

      <div class="surface-card surface-card--compact" style="margin-top: 18px;">
        <p class="section-eyebrow">历史记录与通知</p>
        <div class="timeline-list" style="margin-top: 12px;">
          <article v-for="item in notifications" :key="item.id" class="notification-item">
            <strong>{{ item.title }}</strong>
            <p>{{ item.summary }}</p>
            <span>{{ item.time }}</span>
          </article>
        </div>
      </div>

      <p class="card-copy" style="margin-top: 16px; color: var(--text-faint);">{{ detail.ai.disclaimer }}</p>
    </article>
  </section>
</template>
