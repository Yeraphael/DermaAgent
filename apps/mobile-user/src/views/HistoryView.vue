<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import RiskBadge from '../components/RiskBadge.vue'
import {
  fetchMyConsultations,
  fetchUserNotifications,
  notificationKind,
  type ConsultationSummary,
  type UserNotification,
} from '../services/consultation'

type TimelineFilter = 'ALL' | 'AI' | 'DOCTOR' | 'SYSTEM'

const router = useRouter()
const filter = ref<TimelineFilter>('ALL')
const loading = ref(false)
const errorMessage = ref('')
const consultations = ref<ConsultationSummary[]>([])
const notifications = ref<UserNotification[]>([])

const timeline = computed(() => {
  const consultationItems = consultations.value.map((item) => ({
    id: item.case_id,
    kind: item.doctor_reply ? 'DOCTOR' : 'AI',
    title: item.summary_title,
    summary: item.ai_result?.image_observation || '已生成问诊记录，点击查看详情。',
    meta: item.case_no,
    caseId: item.case_id,
  }))

  const notificationItems = notifications.value.map((item) => ({
    id: item.notification_id,
    kind: notificationKind(item),
    title: item.title,
    summary: item.content,
    meta: item.created_at,
    caseId: item.related_business_id || undefined,
  }))

  return [...consultationItems, ...notificationItems].filter((item) => filter.value === 'ALL' || item.kind === filter.value)
})

function tone(kind: string) {
  if (kind === 'DOCTOR') return 'mint'
  if (kind === 'SYSTEM') return 'violet'
  return 'blue'
}

function kindLabel(kind: string) {
  if (kind === 'DOCTOR') return '医生回复'
  if (kind === 'SYSTEM') return '系统通知'
  return '智能分析'
}

async function loadTimeline() {
  try {
    loading.value = true
    errorMessage.value = ''

    const [caseList, notificationList] = await Promise.all([
      fetchMyConsultations(1, 20),
      fetchUserNotifications(1, 20),
    ])

    consultations.value = caseList.list
    notifications.value = notificationList.list
  } catch (error) {
    errorMessage.value = (error as Error).message
  } finally {
    loading.value = false
  }
}

onMounted(loadTimeline)
</script>

<template>
  <section class="page-stack">
    <article class="surface-card">
      <div class="section-head">
        <div>
          <p class="section-eyebrow">历史记录与通知</p>
          <h1 class="section-title">所有关键节点都收口在同一条时间线</h1>
          <p class="section-subtitle">智能分析、医生回复和系统通知都来自后端真实数据，不再使用演示状态。</p>
        </div>
      </div>
      <div class="segment">
        <button type="button" :class="{ 'is-active': filter === 'ALL' }" @click="filter = 'ALL'">全部</button>
        <button type="button" :class="{ 'is-active': filter === 'AI' }" @click="filter = 'AI'">智能分析</button>
        <button type="button" :class="{ 'is-active': filter === 'DOCTOR' }" @click="filter = 'DOCTOR'">医生回复</button>
        <button type="button" :class="{ 'is-active': filter === 'SYSTEM' }" @click="filter = 'SYSTEM'">系统通知</button>
      </div>
    </article>

    <article v-if="loading" class="surface-card">
      <p class="section-eyebrow">加载中</p>
      <h2 class="card-title">正在拉取历史记录...</h2>
    </article>

    <article v-else-if="errorMessage" class="surface-card">
      <p class="section-eyebrow">加载失败</p>
      <h2 class="card-title">历史时间线加载失败</h2>
      <p class="card-copy">{{ errorMessage }}</p>
      <button type="button" class="primary-button" style="margin-top: 18px;" @click="loadTimeline">重新加载</button>
    </article>

    <div v-else class="timeline-list">
      <article
        v-for="item in timeline"
        :key="`${item.kind}-${item.id}`"
        class="timeline-item"
        @click="item.caseId ? router.push(`/analysis/${item.caseId}`) : undefined"
      >
        <strong>{{ item.title }}</strong>
        <p>{{ item.summary }}</p>
        <div class="action-row" style="margin-top: 12px;">
          <RiskBadge :label="kindLabel(item.kind)" :tone="tone(item.kind)" />
        </div>
        <span>{{ item.meta }}</span>
      </article>
    </div>
  </section>
</template>
