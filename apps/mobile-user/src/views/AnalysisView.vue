<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import ConfirmDialog from '../components/ConfirmDialog.vue'
import PageState from '../components/PageState.vue'
import RiskBadge from '../components/RiskBadge.vue'
import { deleteConsultation, fetchConsultationDetail, fetchMyConsultations, splitTextSegments, type ConsultationDetail } from '../services/consultation'
import {
  formatDateTime,
  getInitial,
  getRiskLabel,
  getRiskTone,
  getStatusLabel,
  getStatusTone,
  parseConsultationNarrative,
  sanitizeVisibleText,
} from '../utils/display'

const props = defineProps<{
  caseId?: string
}>()

const router = useRouter()

const loading = ref(true)
const errorMessage = ref('')
const detail = ref<ConsultationDetail | null>(null)
const activeImageIndex = ref(0)
const deleteDialogOpen = ref(false)
const deleteLoading = ref(false)

const parsedSummary = computed(() => parseConsultationNarrative(detail.value?.chief_complaint))
const activeImage = computed(() => detail.value?.images[activeImageIndex.value] || detail.value?.images[0] || null)
const possibleDirections = computed(() => splitTextSegments(detail.value?.ai_result?.possible_conditions).slice(0, 3))
const careSuggestions = computed(() => splitTextSegments(detail.value?.ai_result?.care_advice))
const imageObservation = computed(() => sanitizeVisibleText(detail.value?.ai_result?.image_observation, '已收到图片，系统正在整理图像观察要点。'))
const riskReminder = computed(() => {
  const message = sanitizeVisibleText(detail.value?.ai_result?.hospital_advice || detail.value?.ai_result?.high_risk_alert)
  if (message) return message
  if (detail.value?.risk_level === 'HIGH') {
    return '若红斑、肿痛、渗液、脓疱或发热等情况持续加重，请尽快线下就诊。'
  }
  return '当前风险可继续结合护理建议观察变化，如症状反复或范围扩大，请及时就诊。'
})
const supportingSymptoms = computed(() => {
  const items: string[] = []
  if (parsedSummary.value.spread) items.push(`扩散情况：${parsedSummary.value.spread}`)
  if (parsedSummary.value.itchLevel) items.push(`瘙痒：${parsedSummary.value.itchLevel}`)
  if (parsedSummary.value.painLevel) items.push(`疼痛：${parsedSummary.value.painLevel}`)
  return items.join('，') || '暂未补充明显伴随症状'
})
const triggerHint = computed(() => {
  if (parsedSummary.value.medication) {
    return `既往处理：${parsedSummary.value.medication}`
  }
  return '暂未明确，可结合近期护肤品更换、饮食、日晒与作息变化继续观察。'
})
const disclaimer = computed(() => sanitizeVisibleText(detail.value?.ai_result?.disclaimer, '基于上传信息与智能模型的综合分析，仅供参考，不能替代面诊诊断。'))

async function loadDetail() {
  try {
    loading.value = true
    errorMessage.value = ''

    let caseId = props.caseId ? Number(props.caseId) : 0
    if (!caseId) {
      const latest = await fetchMyConsultations(1, 1)
      caseId = latest.list[0]?.case_id || 0
    }

    if (!caseId) {
      detail.value = null
      return
    }

    detail.value = await fetchConsultationDetail(caseId)
    activeImageIndex.value = 0
  } catch (error) {
    detail.value = null
    errorMessage.value = (error as Error).message || '加载分析结果失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

function directionBadge(index: number) {
  return ['优先关注', '建议排查', '补充参考'][Math.min(index, 2)]
}

function directionTone(index: number) {
  return index === 0 ? 'rose' : index === 1 ? 'amber' : 'blue'
}

function directionStars(index: number) {
  return ['★★★★☆', '★★★★☆', '★★★☆☆'][Math.min(index, 2)]
}

function openFollowUp() {
  if (!detail.value) return
  const prompt = `我想继续追问病例 ${detail.value.case_no}：${parsedSummary.value.complaint || detail.value.summary_title}`
  router.push({ path: '/qa', query: { ask: prompt } })
}

async function confirmDelete() {
  if (!detail.value) return

  try {
    deleteLoading.value = true
    await deleteConsultation(detail.value.case_id)
    deleteDialogOpen.value = false
    window.alert('删除成功')
    router.replace('/history')
  } catch (error) {
    window.alert((error as Error).message || '删除失败，请稍后重试')
  } finally {
    deleteLoading.value = false
  }
}

watch(
  () => props.caseId,
  () => {
    void loadDetail()
  },
)

onMounted(() => {
  void loadDetail()
})
</script>

<template>
  <section class="page-stack">
    <article class="surface-card">
      <p class="section-eyebrow">智能分析</p>
      <h1 class="section-title">基于上传信息与智能模型的综合分析，仅供参考，不能替代面诊诊断。</h1>
    </article>

    <PageState
      v-if="loading"
      title="正在整理分析结果"
      description="请稍候，我们正在获取病例详情与风险评估。"
    />

    <PageState
      v-else-if="errorMessage"
      tone="error"
      title="分析结果加载失败"
      :description="errorMessage"
      action-text="重新加载"
      @action="loadDetail"
    />

    <PageState
      v-else-if="!detail"
      tone="empty"
      title="当前还没有可查看的分析记录"
      description="完成一次图文问诊后，系统会在这里展示病例摘要、护理建议与医生回复。"
      action-text="去发起问诊"
      @action="router.push('/consultation')"
    />

    <template v-else>
      <article class="surface-card">
        <div class="section-head">
          <div>
            <p class="section-eyebrow">基础信息</p>
            <h2 class="card-title">病例报告</h2>
          </div>
          <RiskBadge :label="getRiskLabel(detail.risk_level)" :tone="getRiskTone(detail.risk_level)" />
        </div>

        <div class="analysis-summary-grid">
          <article class="metric-card">
            <span>病例编号</span>
            <strong>{{ detail.case_no }}</strong>
          </article>
          <article class="metric-card">
            <span>提交时间</span>
            <strong>{{ formatDateTime(detail.submitted_at) }}</strong>
          </article>
          <article class="metric-card">
            <span>分析状态</span>
            <strong>{{ getStatusLabel(detail.status) }}</strong>
          </article>
          <article class="metric-card">
            <span>风险等级</span>
            <strong>{{ getRiskLabel(detail.risk_level) }}</strong>
          </article>
        </div>
      </article>

      <div class="analysis-grid">
        <article class="surface-card">
          <h2 class="card-title">病例摘要</h2>
          <div class="summary-list">
            <div>
              <span>主诉描述</span>
              <p>{{ parsedSummary.complaint || sanitizeVisibleText(detail.summary_title) }}</p>
            </div>
            <div>
              <span>症状部位</span>
              <p>{{ parsedSummary.areas || '未填写' }}</p>
            </div>
            <div>
              <span>病程</span>
              <p>{{ parsedSummary.onsetDuration || detail.onset_duration || '未填写' }}</p>
            </div>
            <div>
              <span>伴随症状</span>
              <p>{{ supportingSymptoms }}</p>
            </div>
            <div>
              <span>诱发因素</span>
              <p>{{ triggerHint }}</p>
            </div>
          </div>
        </article>

        <article class="surface-card">
          <h2 class="card-title">图像观察</h2>
          <div class="analysis-images">
            <div v-if="activeImage" class="analysis-images__main">
              <img :src="activeImage.file_url" :alt="activeImage.file_name || '病例图片'" />
            </div>
            <div v-if="detail.images.length" class="analysis-images__strip">
              <button
                v-for="(image, index) in detail.images.slice(0, 5)"
                :key="image.image_id"
                type="button"
                class="analysis-images__thumb"
                :class="{ 'is-active': activeImageIndex === index }"
                @click="activeImageIndex = index"
              >
                <img :src="image.file_url" :alt="image.file_name || `病例图片 ${index + 1}`" />
              </button>
            </div>
          </div>
          <p class="card-copy">{{ imageObservation }}</p>
        </article>
      </div>

      <div class="analysis-grid">
        <article class="surface-card">
          <h2 class="card-title">可能相关方向</h2>
          <div class="direction-list">
            <article v-for="(item, index) in possibleDirections" :key="item" class="direction-card">
              <div class="direction-card__head">
                <RiskBadge :label="directionBadge(index)" :tone="directionTone(index)" />
                <span>{{ directionStars(index) }}</span>
              </div>
              <strong>{{ sanitizeVisibleText(item) }}</strong>
              <p>
                {{
                  index === 0
                    ? '与当前图片与症状描述匹配度较高，建议优先关注。'
                    : index === 1
                      ? '可结合近期护肤、饮食或环境变化继续排查。'
                      : '可作为补充参考，必要时结合医生面诊进一步确认。'
                }}
              </p>
            </article>

            <article v-if="!possibleDirections.length" class="direction-card">
              <strong>暂未返回明确方向</strong>
              <p>当前可先结合病例摘要、图像观察与风险提醒继续判断。</p>
            </article>
          </div>
        </article>

        <article class="surface-card">
          <h2 class="card-title">护理建议</h2>
          <ul class="analysis-list">
            <li v-for="item in careSuggestions" :key="item">{{ sanitizeVisibleText(item) }}</li>
            <li v-if="!careSuggestions.length">温和清洁、加强保湿、避免刺激，并根据症状变化及时就诊。</li>
          </ul>
        </article>
      </div>

      <div class="analysis-grid">
        <article class="surface-card">
          <h2 class="card-title">就医风险与提醒</h2>
          <div class="risk-panel">
            <div class="risk-panel__head">
              <strong>当前风险：{{ getRiskLabel(detail.risk_level) }}</strong>
              <RiskBadge :label="getRiskLabel(detail.risk_level)" :tone="getRiskTone(detail.risk_level)" />
            </div>
            <p>{{ riskReminder }}</p>
          </div>
        </article>

        <article class="surface-card">
          <h2 class="card-title">医生回复</h2>
          <div v-if="detail.doctor_reply" class="reply-card">
            <div class="reply-card__head">
              <span class="reply-card__avatar">{{ getInitial(detail.doctor_reply.doctor_name) }}</span>
              <div>
                <strong>{{ sanitizeVisibleText(detail.doctor_reply.doctor_name, '皮肤科医师') }}</strong>
                <p>{{ sanitizeVisibleText(detail.doctor?.department, '皮肤科') }}｜{{ formatDateTime(detail.doctor_reply.created_at) }}</p>
              </div>
            </div>
            <p class="reply-card__body">{{ sanitizeVisibleText(detail.doctor_reply.content) }}</p>
            <p v-if="detail.doctor_reply.doctor_remark" class="reply-card__remark">
              {{ sanitizeVisibleText(detail.doctor_reply.doctor_remark) }}
            </p>
          </div>

          <div v-else class="reply-card reply-card--empty">
            <p>医生暂未回复，请耐心等待。收到回复后会在历史记录中同步更新。</p>
          </div>
        </article>
      </div>

      <article class="surface-card analysis-actions">
        <div>
          <p class="section-eyebrow">报告说明</p>
          <p class="card-copy">{{ disclaimer }}</p>
        </div>
        <div class="analysis-actions__buttons">
          <button type="button" class="primary-button" @click="openFollowUp">继续追问</button>
          <button type="button" class="secondary-button" @click="deleteDialogOpen = true">删除记录</button>
        </div>
      </article>
    </template>

    <ConfirmDialog
      :visible="deleteDialogOpen"
      title="确认删除该记录？"
      description="删除后无法恢复。"
      confirm-text="确认删除"
      cancel-text="取消"
      :danger="true"
      :loading="deleteLoading"
      @cancel="deleteDialogOpen = false"
      @confirm="confirmDelete"
    />
  </section>
</template>

<style scoped>
.analysis-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.analysis-summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.analysis-summary-grid .metric-card strong {
  font-size: 18px;
  line-height: 1.5;
}

.summary-list {
  display: grid;
  gap: 14px;
  margin-top: 14px;
}

.summary-list span {
  display: block;
  color: var(--text-faint);
  font-size: 12px;
}

.summary-list p {
  margin: 6px 0 0;
  color: var(--text-main);
  font-size: 14px;
  line-height: 1.85;
}

.analysis-images {
  display: grid;
  gap: 14px;
  margin: 14px 0;
}

.analysis-images__main {
  min-height: 260px;
  padding: 14px;
  border-radius: 18px;
  border: 1px solid var(--border);
  background: rgba(247, 250, 255, 0.98);
}

.analysis-images__main img {
  width: 100%;
  height: 100%;
  max-height: 420px;
  object-fit: contain;
  border-radius: 14px;
  background: #ffffff;
}

.analysis-images__strip {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}

.analysis-images__thumb {
  width: 100%;
  height: 88px;
  padding: 6px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: rgba(248, 250, 255, 0.98);
}

.analysis-images__thumb.is-active {
  border-color: rgba(47, 125, 255, 0.56);
  box-shadow: var(--shadow-sm);
}

.analysis-images__thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 10px;
}

.direction-list {
  display: grid;
  gap: 14px;
  margin-top: 14px;
}

.direction-card {
  padding: 16px;
  border: 1px solid var(--border);
  border-radius: 16px;
  background: rgba(248, 250, 255, 0.98);
}

.direction-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.direction-card strong {
  display: block;
  margin-top: 12px;
  color: var(--text-strong);
  font-size: 16px;
}

.direction-card p {
  margin: 8px 0 0;
  color: var(--text-sub);
  font-size: 14px;
  line-height: 1.8;
}

.analysis-list {
  margin: 14px 0 0;
  padding-left: 18px;
  color: var(--text-main);
  font-size: 14px;
  line-height: 1.9;
}

.analysis-list li + li {
  margin-top: 8px;
}

.risk-panel {
  margin-top: 14px;
  padding: 18px;
  border: 1px solid rgba(242, 156, 56, 0.24);
  border-radius: 18px;
  background: rgba(255, 249, 243, 0.98);
}

.risk-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.risk-panel__head strong {
  color: var(--text-strong);
  font-size: 16px;
}

.risk-panel p {
  margin: 12px 0 0;
  color: var(--text-sub);
  font-size: 14px;
  line-height: 1.85;
}

.reply-card {
  margin-top: 14px;
  padding: 18px;
  border: 1px solid var(--border);
  border-radius: 18px;
  background: rgba(248, 250, 255, 0.98);
}

.reply-card__head {
  display: flex;
  align-items: center;
  gap: 12px;
}

.reply-card__avatar {
  display: inline-grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 14px;
  color: #ffffff;
  font-weight: 700;
  background: var(--gradient-main);
}

.reply-card__head strong {
  display: block;
  color: var(--text-strong);
}

.reply-card__head p,
.reply-card__body,
.reply-card__remark {
  margin: 6px 0 0;
  color: var(--text-sub);
  font-size: 14px;
  line-height: 1.85;
}

.reply-card--empty {
  display: grid;
  place-items: center;
  min-height: 180px;
  text-align: center;
}

.analysis-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.analysis-actions__buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

@media (max-width: 980px) {
  .analysis-grid,
  .analysis-summary-grid,
  .analysis-images__strip {
    grid-template-columns: 1fr;
  }

  .analysis-actions {
    position: sticky;
    bottom: 72px;
    align-items: stretch;
    flex-direction: column;
  }

  .analysis-actions__buttons {
    width: 100%;
  }

  .analysis-actions__buttons button {
    flex: 1;
  }
}
</style>
