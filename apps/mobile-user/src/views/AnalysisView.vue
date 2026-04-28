<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import RiskBadge from '../components/RiskBadge.vue'
import {
  fetchConsultationDetail,
  fetchMyConsultations,
  fetchUserNotifications,
  getConsultationRiskLabel,
  getConsultationStatusLabel,
  splitTextSegments,
  type ConsultationDetail,
  type ConsultationSummary,
  type UserNotification,
} from '../services/consultation'

const props = defineProps<{
  caseId?: string
}>()

const router = useRouter()
const detail = ref<ConsultationDetail | null>(null)
const relatedCases = ref<ConsultationSummary[]>([])
const notifications = ref<UserNotification[]>([])
const loading = ref(false)
const errorMessage = ref('')
const activeImageIndex = ref(0)

const possibleConditions = computed(() => splitTextSegments(detail.value?.ai_result?.possible_conditions))
const careAdvice = computed(() => splitTextSegments(detail.value?.ai_result?.care_advice))
const activeImage = computed(() => detail.value?.images[activeImageIndex.value] || detail.value?.images[0] || null)

function riskTone(risk?: string | null) {
  return risk === 'HIGH' ? 'rose' : risk === 'MEDIUM' ? 'amber' : 'mint'
}

function statusTone(status?: string | null) {
  if (status === 'DOCTOR_REPLIED') return 'mint'
  if (status === 'WAIT_DOCTOR') return 'amber'
  if (status === 'AI_DONE') return 'blue'
  return 'slate'
}

function directionBadge(index: number) {
  return ['优先关注', '重点排查', '补充参考', '延伸参考'][Math.min(index, 3)]
}

function directionTone(index: number) {
  return index === 0 ? 'rose' : index === 1 ? 'amber' : index === 2 ? 'blue' : 'violet'
}

function directionHint(index: number) {
  if (index === 0) return '这一方向与当前图像表现最接近，建议优先对照症状变化观察。'
  if (index === 1) return '如果近期有新护肤品、药膏或环境变化，可以重点排查这一方向。'
  return '可作为补充参考方向，若后续加重再结合医生意见进一步确认。'
}

function careBadge(index: number) {
  return ['立即处理', '日常护理', '观察重点', '补充建议'][Math.min(index, 3)]
}

function careTone(index: number) {
  return index === 0 ? 'blue' : index === 1 ? 'mint' : index === 2 ? 'amber' : 'violet'
}

function careHint(index: number) {
  if (index === 0) return '建议优先执行这一条，再继续观察 24-48 小时内的变化。'
  if (index === 1) return '适合放到日常护理节奏里持续执行，不要间断。'
  return '如果后续出现新的不适或范围扩大，再结合这一条继续调整。'
}

async function loadDetail() {
  try {
    loading.value = true
    errorMessage.value = ''

    const [caseList, notificationList] = await Promise.all([
      fetchMyConsultations(1, 6),
      fetchUserNotifications(1, 6),
    ])

    relatedCases.value = caseList.list
    notifications.value = notificationList.list

    const fallbackCaseId = caseList.list[0]?.case_id
    const targetCaseId = props.caseId ? Number(props.caseId) : fallbackCaseId

    if (!targetCaseId) {
      detail.value = null
      return
    }

    detail.value = await fetchConsultationDetail(targetCaseId)
    activeImageIndex.value = 0
  } catch (error) {
    errorMessage.value = (error as Error).message
    detail.value = null
  } finally {
    loading.value = false
  }
}

watch(() => props.caseId, loadDetail, { immediate: true })
</script>

<template>
  <section v-if="loading" class="page-stack">
    <article class="surface-card">
      <p class="section-eyebrow">加载中</p>
      <h1 class="section-title">正在获取问诊分析结果...</h1>
    </article>
  </section>

  <section v-else-if="errorMessage" class="page-stack">
    <article class="surface-card">
      <p class="section-eyebrow">加载失败</p>
      <h1 class="section-title">分析页加载失败</h1>
      <p class="card-copy">{{ errorMessage }}</p>
      <button type="button" class="primary-button" style="margin-top: 18px;" @click="loadDetail">重试</button>
    </article>
  </section>

  <section v-else-if="detail" class="analysis-layout">
    <article class="surface-card">
      <div class="section-head">
        <div>
          <p class="section-eyebrow">病例摘要</p>
          <h1 class="section-title">{{ detail.summary_title }}</h1>
          <p class="section-subtitle">{{ detail.case_no }} · {{ detail.submitted_at || '刚刚' }}</p>
        </div>
      </div>

      <div class="action-row">
        <RiskBadge :label="getConsultationRiskLabel(detail.risk_level)" :tone="riskTone(detail.risk_level)" />
        <RiskBadge :label="getConsultationStatusLabel(detail.status)" :tone="statusTone(detail.status)" />
      </div>

      <div class="surface-card surface-card--compact" style="margin-top: 18px;">
        <p class="section-eyebrow">症状信息</p>
        <p class="card-copy">{{ detail.chief_complaint }}</p>
        <div class="action-row" style="margin-top: 14px;">
          <RiskBadge :label="`发病时长 · ${detail.onset_duration || '未知'}`" tone="slate" />
          <RiskBadge :label="`瘙痒 · ${detail.itch_level ?? 0}`" tone="violet" />
          <RiskBadge :label="`疼痛 · ${detail.pain_level ?? 0}`" tone="rose" />
        </div>
      </div>

      <div v-if="activeImage" class="analysis-viewer" style="margin-top: 18px;">
        <div class="analysis-viewer__main">
          <img :src="activeImage.file_url" :alt="activeImage.file_name || '问诊图片'" />
        </div>

        <div v-if="detail.images.length > 1" class="analysis-viewer__thumbs">
          <button
            v-for="(item, index) in detail.images"
            :key="item.image_id"
            type="button"
            class="analysis-viewer__thumb"
            :class="{ 'is-active': index === activeImageIndex }"
            @click="activeImageIndex = index"
          >
            <img :src="item.file_url" :alt="item.file_name || `问诊图片 ${index + 1}`" />
          </button>
        </div>
      </div>

      <div class="surface-card surface-card--compact" style="margin-top: 18px;">
        <p class="section-eyebrow">其他病例</p>
        <div class="timeline-list" style="margin-top: 12px;">
          <article
            v-for="item in relatedCases.filter((candidate) => candidate.case_id !== detail.case_id).slice(0, 3)"
            :key="item.case_id"
            class="timeline-item"
            @click="router.push(`/analysis/${item.case_id}`)"
          >
            <strong>{{ item.summary_title }}</strong>
            <p>{{ item.case_no }}</p>
          </article>
        </div>
      </div>
    </article>

    <article class="surface-card">
      <div class="section-head">
        <div>
          <p class="section-eyebrow">智能结果</p>
          <h2 class="card-title">真实多模态分析结果</h2>
        </div>
        <RiskBadge :label="detail.status === 'WAIT_DOCTOR' ? '等待医生复核' : '智能分析已完成'" :tone="detail.status === 'WAIT_DOCTOR' ? 'amber' : 'mint'" />
      </div>

      <div class="surface-card surface-card--compact">
        <p class="section-eyebrow">图像观察</p>
        <p class="card-copy">{{ detail.ai_result?.image_observation || '当前尚未返回图像观察结果。' }}</p>
      </div>

      <div class="surface-card surface-card--compact" style="margin-top: 18px;">
        <p class="section-eyebrow">可能相关方向</p>
        <div class="result-stack" style="margin-top: 14px;">
          <article v-for="(item, index) in possibleConditions" :key="item" class="result-item">
            <div class="result-item__index">{{ String(index + 1).padStart(2, '0') }}</div>
            <div class="result-item__content">
              <div class="result-item__meta">
                <RiskBadge :label="directionBadge(index)" :tone="directionTone(index)" />
              </div>
              <h3 class="result-item__title">{{ item }}</h3>
              <p class="result-item__copy">{{ directionHint(index) }}</p>
            </div>
          </article>

          <article v-if="!possibleConditions.length" class="result-item result-item--single">
            <div class="result-item__content">
              <div class="result-item__meta">
                <RiskBadge label="信息不足" tone="slate" />
              </div>
              <h3 class="result-item__title">暂未返回明确方向</h3>
              <p class="result-item__copy">当前病例没有结构化方向列表，可先结合图像观察与风险提醒继续判断。</p>
            </div>
          </article>
        </div>
      </div>

      <div class="surface-card surface-card--compact" style="margin-top: 18px;">
        <p class="section-eyebrow">护理建议</p>
        <div class="result-stack" style="margin-top: 14px;">
          <article v-for="(item, index) in careAdvice" :key="item" class="result-item">
            <div class="result-item__index">{{ String(index + 1).padStart(2, '0') }}</div>
            <div class="result-item__content">
              <div class="result-item__meta">
                <RiskBadge :label="careBadge(index)" :tone="careTone(index)" />
              </div>
              <h3 class="result-item__title">{{ item }}</h3>
              <p class="result-item__copy">{{ careHint(index) }}</p>
            </div>
          </article>

          <article v-if="!careAdvice.length" class="result-item result-item--single">
            <div class="result-item__content">
              <div class="result-item__meta">
                <RiskBadge label="等待补充" tone="slate" />
              </div>
              <h3 class="result-item__title">暂未返回护理建议</h3>
              <p class="result-item__copy">当前病例还没有结构化护理建议，可先关注图像观察和风险提醒。</p>
            </div>
          </article>
        </div>
      </div>

      <div class="surface-card surface-card--compact" style="margin-top: 18px;">
        <p class="section-eyebrow">就医 / 风险提醒</p>
        <p class="card-copy">{{ detail.ai_result?.hospital_advice || detail.ai_result?.high_risk_alert || '当前暂无紧急风险提醒。' }}</p>
        <div class="action-row" style="margin-top: 12px;">
          <RiskBadge :label="detail.risk_level === 'HIGH' ? '建议线下就医' : '按建议继续观察'" :tone="detail.risk_level === 'HIGH' ? 'rose' : 'mint'" />
        </div>
      </div>
    </article>

    <article class="surface-card">
      <div class="section-head">
        <div>
          <p class="section-eyebrow">医生 / 通知</p>
          <h2 class="card-title">跟进与追踪</h2>
        </div>
      </div>

      <div v-if="detail.doctor_reply" class="surface-card surface-card--compact">
        <p class="section-eyebrow">医生回复</p>
        <h3 class="card-title" style="font-size: 26px; margin-top: 8px;">{{ detail.doctor_reply.doctor_name }}</h3>
        <p class="section-subtitle">{{ detail.doctor?.department || '皮肤科' }} · {{ detail.doctor_reply.created_at }}</p>
        <p class="card-copy">{{ detail.doctor_reply.content }}</p>
        <p v-if="detail.doctor_reply.doctor_remark" class="card-copy" style="margin-top: 12px;">{{ detail.doctor_reply.doctor_remark }}</p>
      </div>

      <div v-else class="surface-card surface-card--compact">
        <p class="section-eyebrow">医生回复</p>
        <p class="card-copy">当前还没有医生回复。如果病例属于高风险，后端已经自动放入医生复核队列。</p>
      </div>

      <div class="surface-card surface-card--compact" style="margin-top: 18px;">
        <p class="section-eyebrow">最近通知</p>
        <div class="timeline-list" style="margin-top: 12px;">
          <article v-for="item in notifications.slice(0, 4)" :key="item.notification_id" class="notification-item">
            <strong>{{ item.title }}</strong>
            <p>{{ item.content }}</p>
            <span>{{ item.created_at }}</span>
          </article>
        </div>
      </div>

      <p class="card-copy" style="margin-top: 16px; color: var(--text-sub);">
        {{ detail.ai_result?.disclaimer || '本分析结果仅用于健康辅助与分诊，不替代临床诊断。' }}
      </p>
    </article>
  </section>

  <section v-else class="page-stack">
    <article class="surface-card">
      <p class="section-eyebrow">暂无数据</p>
      <h1 class="section-title">当前还没有可查看的问诊记录。</h1>
      <button type="button" class="primary-button" style="margin-top: 18px;" @click="router.push('/consultation')">创建第一条问诊</button>
    </article>
  </section>
</template>
