<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'

import EmptyState from '@/components/EmptyState.vue'
import PanelCard from '@/components/PanelCard.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import {
  getConsultationStatusLabel,
  getDoctorConsultationList,
  getRiskLabel,
  saveDoctorAiFeedback,
  saveDoctorReply,
  type ConsultationRecord,
} from '@/data/controlCenter'

type EnrichedConsultation = Awaited<ReturnType<typeof getDoctorConsultationList>>[number]

const route = useRoute()
const router = useRouter()

const cases = ref<EnrichedConsultation[]>([])
const loading = ref(false)
const statusFilter = ref<'ALL' | ConsultationRecord['status']>('ALL')
const keyword = ref('')

const replyForm = reactive({
  first_impression: '',
  care_advice: '',
  suggest_offline: false,
  suggest_revisit: true,
  note: '',
})

const feedbackForm = reactive({
  accuracy: 'ACCURATE' as 'ACCURATE' | 'PARTIAL' | 'INACCURATE',
  note: '',
})

const statusOptions: Array<{ label: string; value: 'ALL' | ConsultationRecord['status'] }> = [
  { label: '全部', value: 'ALL' },
  { label: '待医生处理', value: 'WAIT_DOCTOR' },
  { label: '医生已回复', value: 'DOCTOR_REPLIED' },
  { label: 'AI 已完成', value: 'AI_DONE' },
  { label: '已关闭', value: 'CLOSED' },
]

const accuracyOptions = [
  { label: '准确', value: 'ACCURATE' as const },
  { label: '部分准确', value: 'PARTIAL' as const },
  { label: '不准确', value: 'INACCURATE' as const },
]

function statusTone(status: string) {
  if (status === 'WAIT_DOCTOR') return 'amber'
  if (status === 'DOCTOR_REPLIED') return 'mint'
  if (status === 'AI_DONE') return 'blue'
  return 'slate'
}

function riskTone(risk: string) {
  if (risk === 'HIGH') return 'rose'
  if (risk === 'MEDIUM') return 'amber'
  return 'mint'
}

const filteredCases = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  return cases.value.filter((item) => {
    const matchesStatus = statusFilter.value === 'ALL' || item.status === statusFilter.value
    const matchesQuery =
      !query ||
      item.case_no.toLowerCase().includes(query) ||
      item.summary_title.toLowerCase().includes(query) ||
      item.patient.name.toLowerCase().includes(query)
    return matchesStatus && matchesQuery
  })
})

const selectedCase = computed(() => {
  const routeId = Number(route.params.id)
  if (routeId) {
    return filteredCases.value.find((item) => item.case_id === routeId) || null
  }
  return filteredCases.value[0] || null
})

watch(
  () => selectedCase.value?.case_id,
  () => {
    if (!selectedCase.value) return
    replyForm.first_impression = selectedCase.value.doctor_reply?.first_impression || ''
    replyForm.care_advice = selectedCase.value.doctor_reply?.care_advice || selectedCase.value.ai_result.advice.join('；')
    replyForm.suggest_offline = selectedCase.value.doctor_reply?.suggest_offline || selectedCase.value.risk_level === 'HIGH'
    replyForm.suggest_revisit = selectedCase.value.doctor_reply?.suggest_revisit ?? true
    replyForm.note = selectedCase.value.doctor_reply?.note || ''
    feedbackForm.accuracy = selectedCase.value.ai_feedback?.accuracy || 'ACCURATE'
    feedbackForm.note = selectedCase.value.ai_feedback?.note || ''
  },
  { immediate: true },
)

async function loadCases() {
  loading.value = true
  cases.value = await getDoctorConsultationList()
  loading.value = false
}

function setStatusFilter(value: 'ALL' | ConsultationRecord['status']) {
  statusFilter.value = value
}

function selectCase(caseId: number) {
  router.replace(`/doctor/consultations/${caseId}`)
}

async function submitReply() {
  if (!selectedCase.value) return
  await saveDoctorReply(selectedCase.value.case_id, { ...replyForm })
  await loadCases()
  ElMessage.success('医生回复已提交。')
}

async function submitFeedback() {
  if (!selectedCase.value) return
  await saveDoctorAiFeedback(selectedCase.value.case_id, { ...feedbackForm })
  await loadCases()
  ElMessage.success('AI 反馈已保存。')
}

onMounted(loadCases)
</script>

<template>
  <section class="three-column">
    <PanelCard title="问诊列表" subtitle="左侧列表、中心详情、右侧回复面板统一到同一套高级清晰的布局。">
      <template #actions>
        <div class="segment">
          <button
            v-for="item in statusOptions"
            :key="item.value"
            type="button"
            class="segment-button"
            :class="{ 'is-active': statusFilter === item.value }"
            @click="setStatusFilter(item.value)"
          >
            {{ item.label }}
          </button>
        </div>
      </template>

      <div class="form-field">
        <label>搜索患者姓名、病例号或摘要</label>
        <input v-model="keyword" class="ghost-input" placeholder="例如：李晚雨 / 2026-0621 / 泛红" />
      </div>

      <div class="list-panel" style="margin-top: 18px;">
        <article
          v-for="item in filteredCases"
          :key="item.case_id"
          class="list-row"
          :class="{ 'is-active': selectedCase?.case_id === item.case_id }"
          @click="selectCase(item.case_id)"
        >
          <div class="list-row__head">
            <div class="avatar-row">
              <img :src="item.patient.avatar" :alt="item.patient.name" />
              <div>
                <strong>{{ item.patient.name }}</strong>
                <span>{{ item.patient.gender }} · {{ item.patient.age }} 岁</span>
              </div>
            </div>
            <span class="tiny-label">{{ item.submitted_at }}</span>
          </div>
          <p class="list-row__summary">{{ item.summary_title }}</p>
          <div class="action-row" style="margin-top: 12px;">
            <StatusBadge :label="getConsultationStatusLabel(item.status)" :tone="statusTone(item.status)" />
            <StatusBadge :label="getRiskLabel(item.risk_level)" :tone="riskTone(item.risk_level)" />
          </div>
        </article>
      </div>
    </PanelCard>

    <PanelCard v-if="selectedCase" title="问诊详情" subtitle="患者资料、上传图片、AI 结果与风险等级在中栏一屏完成。">
      <div class="detail-grid">
        <article class="detail-card">
          <div class="avatar-row">
            <img :src="selectedCase.patient.avatar" :alt="selectedCase.patient.name" />
            <div>
              <strong>{{ selectedCase.patient.name }}</strong>
              <span>{{ selectedCase.patient.gender }} · {{ selectedCase.patient.age }} 岁 · {{ selectedCase.patient.city }}</span>
            </div>
          </div>
          <div class="pill-stack" style="margin-top: 14px;">
            <StatusBadge v-for="tag in selectedCase.patient.tags" :key="tag" :label="tag" tone="blue" />
          </div>
        </article>

        <article class="detail-card">
          <div class="tiny-label">病例编号</div>
          <strong>{{ selectedCase.case_no }}</strong>
          <p class="detail-copy">{{ selectedCase.summary_title }}</p>
          <div class="action-row" style="margin-top: 10px;">
            <StatusBadge :label="getConsultationStatusLabel(selectedCase.status)" :tone="statusTone(selectedCase.status)" />
            <StatusBadge :label="getRiskLabel(selectedCase.risk_level)" :tone="riskTone(selectedCase.risk_level)" />
          </div>
        </article>
      </div>

      <div class="detail-card" style="margin-top: 18px;">
        <div class="tiny-label">症状描述</div>
        <p class="detail-copy">{{ selectedCase.symptom_summary }}</p>
        <div class="pill-stack" style="margin-top: 14px;">
          <StatusBadge :label="`发病时长 · ${selectedCase.onset_duration}`" tone="slate" />
          <StatusBadge :label="`瘙痒 ${selectedCase.itch_level} / 5`" tone="violet" />
          <StatusBadge :label="`疼痛 ${selectedCase.pain_level} / 5`" tone="rose" />
          <StatusBadge :label="selectedCase.spread_flag ? `扩散部位 · ${selectedCase.spread_parts.join('、')}` : '暂无扩散'" tone="blue" />
        </div>
      </div>

      <div class="media-strip" style="margin-top: 18px;">
        <img v-for="item in selectedCase.images" :key="item" :src="item" alt="skin upload" />
      </div>

      <div class="detail-card" style="margin-top: 18px;">
        <div class="detail-row">
          <div>
            <div class="tiny-label">AI 分析结果</div>
            <p class="detail-title">{{ selectedCase.ai_result.condition_guess }}</p>
          </div>
          <StatusBadge :label="`置信度 ${selectedCase.ai_result.confidence}%`" tone="blue" />
        </div>
        <p class="detail-copy">{{ selectedCase.ai_result.image_observation }}</p>
        <div class="progress-list" style="margin-top: 18px;">
          <div
            v-for="item in selectedCase.ai_result.possible_directions"
            :key="item.label"
            class="progress-item"
          >
            <span>{{ item.label }}</span>
            <div class="progress-track"><span :style="{ width: `${item.value}%` }" /></div>
            <strong>{{ item.value }}%</strong>
          </div>
        </div>
        <div class="detail-card" style="margin-top: 18px; padding: 18px;">
          <div class="tiny-label">护理建议</div>
          <div class="key-value" style="margin-top: 10px;">
            <div v-for="item in selectedCase.ai_result.advice" :key="item" class="key-value__row">
              <span>建议</span>
              <strong>{{ item }}</strong>
            </div>
          </div>
        </div>
      </div>
    </PanelCard>

    <PanelCard v-if="selectedCase" title="医生回复与 AI 反馈" subtitle="回复表单、是否建议线下就医和 AI 结果反馈放在同一块操作区。">
      <div class="doctor-response-grid">
        <div class="form-field">
          <label>初步意见</label>
          <textarea v-model="replyForm.first_impression" class="ghost-textarea" placeholder="请输入医生的初步判断…" />
        </div>
        <div class="form-field">
          <label>护理建议</label>
          <textarea v-model="replyForm.care_advice" class="ghost-textarea" placeholder="请输入护理建议…" />
        </div>

        <div class="split-grid">
          <div class="form-field">
            <label>是否建议线下就医</label>
            <div class="segment">
              <button type="button" class="segment-button" :class="{ 'is-active': !replyForm.suggest_offline }" @click="replyForm.suggest_offline = false">暂不建议</button>
              <button type="button" class="segment-button" :class="{ 'is-active': replyForm.suggest_offline }" @click="replyForm.suggest_offline = true">建议尽快就医</button>
            </div>
          </div>
          <div class="form-field">
            <label>是否建议复查</label>
            <div class="segment">
              <button type="button" class="segment-button" :class="{ 'is-active': !replyForm.suggest_revisit }" @click="replyForm.suggest_revisit = false">无需复查</button>
              <button type="button" class="segment-button" :class="{ 'is-active': replyForm.suggest_revisit }" @click="replyForm.suggest_revisit = true">建议复查</button>
            </div>
          </div>
        </div>

        <div class="form-field">
          <label>医生备注</label>
          <textarea v-model="replyForm.note" class="ghost-textarea" placeholder="记录给患者的附加提醒，或仅医生可见的备注…" />
        </div>
        <button type="button" class="primary-button" @click="submitReply">提交回复</button>
      </div>

      <div class="detail-card" style="margin-top: 18px;">
        <div class="tiny-label">AI 结果反馈</div>
        <p class="detail-copy">本次 AI 分析对医生判断是否有帮助？反馈结果会影响后台准确率统计与后续 Prompt 调优。</p>
        <div class="action-row" style="margin-top: 14px;">
          <button
            v-for="item in accuracyOptions"
            :key="item.value"
            type="button"
            class="segment-button"
            :class="{ 'is-active': feedbackForm.accuracy === item.value }"
            @click="feedbackForm.accuracy = item.value"
          >
            {{ item.label }}
          </button>
        </div>
        <div class="form-field" style="margin-top: 14px;">
          <label>修正意见</label>
          <textarea v-model="feedbackForm.note" class="ghost-textarea" placeholder="例如：AI 对泛红原因判断准确，但对扩散趋势敏感度偏低…" />
        </div>
        <button type="button" class="ghost-button" @click="submitFeedback">保存 AI 反馈</button>
      </div>
    </PanelCard>

    <PanelCard v-else title="暂无匹配病例" subtitle="换一个筛选条件试试，或者回到工作台查看优先队列。">
      <EmptyState title="没有找到匹配的问诊" copy="你可以切换状态、清空搜索词，或先返回工作台查看当前重点病例。" />
    </PanelCard>
  </section>
</template>
