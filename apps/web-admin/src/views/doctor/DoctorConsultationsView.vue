<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'

import EmptyState from '@/components/EmptyState.vue'
import PanelCard from '@/components/PanelCard.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import {
  fetchDoctorConsultationDetail,
  fetchDoctorConsultations,
  submitDoctorAIFeedback,
  submitDoctorReply,
  type ConsultationDetail,
} from '@/api/workspace'
import {
  accuracyLabel,
  accuracyTone,
  cleanVisibleText,
  formatDateTime,
  riskLabel,
  riskTone,
  resolveAvatar,
  splitVisibleText,
  statusLabel,
  statusTone,
  yesNoLabel,
} from '@/utils/workspace'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const detailLoading = ref(false)
const replySubmitting = ref(false)
const feedbackSubmitting = ref(false)
const selectedImageIndex = ref(0)

const filters = reactive({
  status: '',
  risk_level: '',
  keyword: '',
})

const list = ref<ConsultationDetail[]>([])
const detail = ref<ConsultationDetail | null>(null)

const replyForm = reactive({
  first_impression: '',
  care_advice: '',
  suggest_offline_visit: true,
  suggest_follow_up: true,
  doctor_remark: '',
})

const feedbackForm = reactive({
  ai_accuracy: 'ACCURATE',
  correction_note: '',
  knowledge_gap_note: '',
})

const selectedImage = computed(() => {
  const images = detail.value?.images || []
  return images[selectedImageIndex.value]?.file_url || images[0]?.file_url || ''
})

const directionItems = computed(() => {
  const items = detail.value?.ai_result?.possible_conditions_list
    || splitVisibleText(detail.value?.ai_result?.possible_conditions)
  const presets = [45, 30, 18, 12]
  return items.slice(0, 4).map((label, index) => ({
    label,
    percent: presets[index] || 10,
  }))
})

const careItems = computed(() => {
  return detail.value?.ai_result?.care_advice_list
    || splitVisibleText(detail.value?.ai_result?.care_advice)
})

function syncForms() {
  replyForm.first_impression = detail.value?.doctor_reply?.first_impression || ''
  replyForm.care_advice = detail.value?.doctor_reply?.care_advice || careItems.value.join('；')
  replyForm.suggest_offline_visit = Boolean(detail.value?.doctor_reply?.suggest_offline_visit ?? (detail.value?.risk_level === 'HIGH'))
  replyForm.suggest_follow_up = Boolean(detail.value?.doctor_reply?.suggest_follow_up ?? 1)
  replyForm.doctor_remark = detail.value?.doctor_reply?.doctor_remark || ''

  feedbackForm.ai_accuracy = detail.value?.ai_feedback?.ai_accuracy || 'ACCURATE'
  feedbackForm.correction_note = detail.value?.ai_feedback?.correction_note || ''
  feedbackForm.knowledge_gap_note = detail.value?.ai_feedback?.knowledge_gap_note || ''
}

async function loadList() {
  try {
    loading.value = true
    const result = await fetchDoctorConsultations({
      page: 1,
      page_size: 40,
      status: filters.status || undefined,
      risk_level: filters.risk_level || undefined,
      keyword: filters.keyword || undefined,
    })
    list.value = result.list

    const routeId = Number(route.params.id)
    const matched = routeId ? result.list.find((item) => item.case_id === routeId) : null
    const targetId = matched?.case_id || result.list[0]?.case_id
    if (targetId && targetId !== routeId) {
      router.replace(`/doctor/consultations/${targetId}`)
    } else if (!targetId) {
      detail.value = null
    }
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    loading.value = false
  }
}

async function loadDetail(caseId: number) {
  try {
    detailLoading.value = true
    detail.value = await fetchDoctorConsultationDetail(caseId)
    selectedImageIndex.value = 0
    syncForms()
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    detailLoading.value = false
  }
}

function selectCase(caseId: number) {
  router.replace(`/doctor/consultations/${caseId}`)
}

function openPatient() {
  const userId = detail.value?.patient?.account?.account_id
  if (!userId) return
  router.push(`/doctor/patients/${userId}`)
}

async function refreshAll() {
  await loadList()
  const routeId = Number(route.params.id)
  if (routeId) {
    await loadDetail(routeId)
  }
}

async function submitReplyForm() {
  if (!detail.value) return
  try {
    replySubmitting.value = true
    await submitDoctorReply(detail.value.case_id, {
      first_impression: replyForm.first_impression,
      care_advice: replyForm.care_advice,
      suggest_offline_visit: replyForm.suggest_offline_visit ? 1 : 0,
      suggest_follow_up: replyForm.suggest_follow_up ? 1 : 0,
      doctor_remark: replyForm.doctor_remark,
    })
    await refreshAll()
    ElMessage.success('医生回复已提交。')
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    replySubmitting.value = false
  }
}

async function submitFeedbackForm() {
  if (!detail.value) return
  try {
    feedbackSubmitting.value = true
    await submitDoctorAIFeedback(detail.value.case_id, {
      ai_accuracy: feedbackForm.ai_accuracy,
      correction_note: feedbackForm.correction_note,
      knowledge_gap_note: feedbackForm.knowledge_gap_note,
    })
    await refreshAll()
    ElMessage.success('AI 反馈已保存。')
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    feedbackSubmitting.value = false
  }
}

watch(
  () => route.params.id,
  async (value) => {
    const caseId = Number(value)
    if (caseId) {
      await loadDetail(caseId)
    }
  },
)

onMounted(loadList)
</script>

<template>
  <section class="three-column">
    <PanelCard title="问诊列表" subtitle="查看待处理、已回复与高风险问诊，并可按患者信息快速筛选。">
      <div class="filters-grid">
        <el-select v-model="filters.status" clearable placeholder="问诊状态">
          <el-option label="待医生处理" value="WAIT_DOCTOR" />
          <el-option label="医生已回复" value="DOCTOR_REPLIED" />
          <el-option label="AI 已完成" value="AI_DONE" />
          <el-option label="已关闭" value="CLOSED" />
        </el-select>
        <el-select v-model="filters.risk_level" clearable placeholder="风险等级">
          <el-option label="低风险" value="LOW" />
          <el-option label="中风险" value="MEDIUM" />
          <el-option label="高风险" value="HIGH" />
        </el-select>
      </div>

      <div class="form-field" style="margin-top: 14px;">
        <label>搜索患者、病例号或症状摘要</label>
        <input
          v-model="filters.keyword"
          class="ghost-input"
          placeholder="例如：李婉晴 / 2026-000128 / 面部泛红"
          @keydown.enter.prevent="loadList"
        />
      </div>

      <div class="action-row" style="margin-top: 14px;">
        <button type="button" class="primary-button" @click="loadList">刷新列表</button>
      </div>

      <div v-if="list.length" class="list-panel" style="margin-top: 18px;">
        <article
          v-for="item in list"
          :key="item.case_id"
          class="list-row"
          :class="{ 'is-active': detail?.case_id === item.case_id }"
          @click="selectCase(item.case_id)"
        >
          <div class="list-row__head">
            <div>
              <strong>{{ item.patient?.profile?.real_name || item.patient?.account?.username || '患者' }}</strong>
              <span>{{ item.patient?.profile?.gender || '未设置' }} · {{ item.patient?.profile?.age || '--' }} 岁</span>
            </div>
            <span class="tiny-label">{{ formatDateTime(item.submitted_at) }}</span>
          </div>

          <p class="list-row__summary">{{ cleanVisibleText(item.summary_title, '待补充摘要') }}</p>
          <div class="action-row" style="margin-top: 12px;">
            <StatusBadge :label="riskLabel(item.risk_level)" :tone="riskTone(item.risk_level)" />
            <StatusBadge :label="statusLabel(item.status)" :tone="statusTone(item.status)" />
          </div>
        </article>
      </div>
      <EmptyState v-else title="当前没有匹配问诊" copy="你可以切换筛选条件，或返回工作台查看优先处理队列。" />
    </PanelCard>

    <PanelCard v-if="detail" title="问诊详情" subtitle="患者信息、图像、AI 分析结果与病情概览集中展示。">
      <div v-loading="detailLoading">
        <div class="detail-grid">
          <article class="detail-card">
            <div class="avatar-row">
              <img :src="resolveAvatar(detail.patient?.account?.avatar_url, detail.patient?.profile?.real_name || detail.patient?.account?.username, 'mint')" :alt="detail.patient?.profile?.real_name || '患者'" />
              <div>
                <strong>{{ detail.patient?.profile?.real_name || detail.patient?.account?.username || '患者' }}</strong>
                <span>
                  {{ detail.patient?.profile?.gender || '未设置' }} · {{ detail.patient?.profile?.age || '--' }} 岁
                  · {{ detail.patient?.profile?.city || '未设置城市' }}
                </span>
              </div>
            </div>
            <div class="pill-stack" style="margin-top: 14px;">
              <StatusBadge v-for="tag in detail.patient?.tags || []" :key="tag" :label="tag" tone="blue" />
            </div>
          </article>

          <article class="detail-card">
            <div class="tiny-label">病例编号</div>
            <strong>{{ detail.case_no }}</strong>
            <p class="detail-copy">{{ cleanVisibleText(detail.summary_title, '待补充摘要') }}</p>
            <div class="action-row" style="margin-top: 12px;">
              <StatusBadge :label="riskLabel(detail.risk_level)" :tone="riskTone(detail.risk_level)" />
              <StatusBadge :label="statusLabel(detail.status)" :tone="statusTone(detail.status)" />
              <StatusBadge v-if="detail.ai_confidence" :label="`置信度 ${Math.round(detail.ai_confidence * 100)}%`" tone="mint" />
            </div>
          </article>
        </div>

        <div class="detail-card" style="margin-top: 18px;">
          <div class="tiny-label">症状概览</div>
          <p class="detail-copy">{{ cleanVisibleText(detail.chief_complaint, '患者尚未补充完整症状描述。') }}</p>
          <div class="pill-stack" style="margin-top: 14px;">
            <StatusBadge :label="`发病时长 ${detail.onset_duration || '未填写'}`" tone="slate" />
            <StatusBadge :label="`瘙痒 ${detail.itch_level ?? 0} / 5`" tone="violet" />
            <StatusBadge :label="`疼痛 ${detail.pain_level ?? 0} / 5`" tone="rose" />
            <StatusBadge :label="detail.spread_flag ? '存在扩散' : '暂无扩散'" :tone="detail.spread_flag ? 'amber' : 'mint'" />
          </div>
        </div>

        <div class="case-gallery" style="margin-top: 18px;">
          <div class="case-gallery__main">
            <img v-if="selectedImage" :src="selectedImage" :alt="detail.summary_title" />
            <div v-else class="gallery-empty">暂无上传图片</div>
          </div>
          <div v-if="detail.images.length > 1" class="case-gallery__thumbs">
            <button
              v-for="(item, index) in detail.images"
              :key="item.image_id"
              type="button"
              class="case-gallery__thumb"
              :class="{ 'is-active': selectedImageIndex === index }"
              @click="selectedImageIndex = index"
            >
              <img :src="item.file_url" :alt="item.file_name" />
            </button>
          </div>
        </div>

        <div class="detail-card" style="margin-top: 18px;">
          <div class="detail-row">
            <div>
              <div class="tiny-label">AI 分析结果参考</div>
              <p class="detail-title">{{ riskLabel(detail.ai_result?.risk_level || detail.risk_level) }}</p>
            </div>
            <StatusBadge
              :label="detail.ai_result?.analysis_status === 'SUCCESS' ? '分析完成' : '结果已生成'"
              tone="blue"
            />
          </div>
          <p class="detail-copy">{{ cleanVisibleText(detail.ai_result?.image_observation, '系统正在整理图像观察结论。') }}</p>

          <div class="insight-stack" style="margin-top: 18px;">
            <article v-for="(item, index) in directionItems" :key="item.label" class="insight-card">
              <div class="insight-card__rank">{{ String(index + 1).padStart(2, '0') }}</div>
              <div class="insight-card__body">
                <div class="insight-card__meta">
                  <StatusBadge :label="item.label" tone="violet" />
                  <StatusBadge :label="`${item.percent}%`" tone="slate" />
                </div>
                <div class="insight-card__meter"><span :style="{ width: `${item.percent}%` }" /></div>
              </div>
            </article>
          </div>

          <div v-if="careItems.length" class="insight-stack" style="margin-top: 18px;">
            <article v-for="(item, index) in careItems" :key="item" class="insight-card insight-card--single">
              <div class="insight-card__body">
                <div class="insight-card__meta">
                  <StatusBadge :label="`护理建议 ${index + 1}`" tone="mint" />
                </div>
                <p class="insight-card__copy">{{ item }}</p>
              </div>
            </article>
          </div>

          <div class="detail-card" style="margin-top: 18px; padding: 18px;">
            <div class="tiny-label">线下就医建议</div>
            <p class="detail-copy">{{ cleanVisibleText(detail.ai_result?.hospital_advice || detail.ai_result?.high_risk_alert, '如症状持续加重、范围扩大或伴随明显不适，请尽快线下就医。') }}</p>
          </div>
        </div>
      </div>
    </PanelCard>

    <PanelCard v-if="detail" title="医生回复与 AI 反馈" subtitle="在同一侧操作区完成专业回复、护理建议与结果反馈。">
      <div class="doctor-response-grid">
        <div class="form-field">
          <label>初步意见</label>
          <textarea v-model="replyForm.first_impression" class="ghost-textarea" placeholder="请输入医生的专业判断与当前建议" />
        </div>

        <div class="form-field">
          <label>护理建议</label>
          <textarea v-model="replyForm.care_advice" class="ghost-textarea" placeholder="请输入日常护理、观察重点或用药提醒" />
        </div>

        <div class="split-grid">
          <div class="form-field">
            <label>是否建议线下就医</label>
            <div class="segment">
              <button
                type="button"
                class="segment-button"
                :class="{ 'is-active': replyForm.suggest_offline_visit }"
                @click="replyForm.suggest_offline_visit = true"
              >
                建议
              </button>
              <button
                type="button"
                class="segment-button"
                :class="{ 'is-active': !replyForm.suggest_offline_visit }"
                @click="replyForm.suggest_offline_visit = false"
              >
                暂不建议
              </button>
            </div>
          </div>

          <div class="form-field">
            <label>是否建议复查</label>
            <div class="segment">
              <button
                type="button"
                class="segment-button"
                :class="{ 'is-active': replyForm.suggest_follow_up }"
                @click="replyForm.suggest_follow_up = true"
              >
                建议复查
              </button>
              <button
                type="button"
                class="segment-button"
                :class="{ 'is-active': !replyForm.suggest_follow_up }"
                @click="replyForm.suggest_follow_up = false"
              >
                暂不需要
              </button>
            </div>
          </div>
        </div>

        <div class="form-field">
          <label>医生备注</label>
          <textarea v-model="replyForm.doctor_remark" class="ghost-textarea" placeholder="补充提醒、复诊建议或仅医生可见备注" />
        </div>

        <div class="action-row">
          <button type="button" class="primary-button" :disabled="replySubmitting" @click="submitReplyForm">
            {{ replySubmitting ? '提交中…' : '提交回复' }}
          </button>
          <button type="button" class="ghost-button" @click="openPatient">查看患者档案</button>
        </div>
      </div>

      <div class="detail-card" style="margin-top: 18px;">
        <div class="detail-row">
          <div>
            <div class="tiny-label">AI 结果反馈</div>
            <p class="detail-copy">本次分析结果是否对你的专业判断有帮助？保存后会同步进入平台统计。</p>
          </div>
          <StatusBadge
            :label="accuracyLabel(detail.ai_feedback?.ai_accuracy)"
            :tone="accuracyTone(detail.ai_feedback?.ai_accuracy)"
          />
        </div>

        <div class="action-row" style="margin-top: 14px;">
          <button
            type="button"
            class="segment-button"
            :class="{ 'is-active': feedbackForm.ai_accuracy === 'ACCURATE' }"
            @click="feedbackForm.ai_accuracy = 'ACCURATE'"
          >
            准确
          </button>
          <button
            type="button"
            class="segment-button"
            :class="{ 'is-active': feedbackForm.ai_accuracy === 'PARTIAL' }"
            @click="feedbackForm.ai_accuracy = 'PARTIAL'"
          >
            部分准确
          </button>
          <button
            type="button"
            class="segment-button"
            :class="{ 'is-active': feedbackForm.ai_accuracy === 'INACCURATE' }"
            @click="feedbackForm.ai_accuracy = 'INACCURATE'"
          >
            不准确
          </button>
        </div>

        <div class="form-field" style="margin-top: 14px;">
          <label>修正意见</label>
          <textarea v-model="feedbackForm.correction_note" class="ghost-textarea" placeholder="例如：病因方向合理，但对扩散风险判断偏保守" />
        </div>

        <div class="form-field">
          <label>知识缺口或建议补充</label>
          <textarea v-model="feedbackForm.knowledge_gap_note" class="ghost-textarea" placeholder="记录希望 AI 后续增强的知识点、提示或风险判断维度" />
        </div>

        <button type="button" class="ghost-button" :disabled="feedbackSubmitting" @click="submitFeedbackForm">
          {{ feedbackSubmitting ? '保存中…' : '保存 AI 反馈' }}
        </button>
      </div>

      <div v-if="detail.doctor_reply" class="detail-card" style="margin-top: 18px;">
        <div class="tiny-label">已保存的医生回复</div>
        <p class="detail-copy">{{ cleanVisibleText(detail.doctor_reply.content) }}</p>
        <div class="pill-stack" style="margin-top: 14px;">
          <StatusBadge :label="yesNoLabel(detail.doctor_reply.suggest_offline_visit, '建议线下就医', '暂不建议线下就医')" :tone="detail.doctor_reply.suggest_offline_visit ? 'amber' : 'mint'" />
          <StatusBadge :label="yesNoLabel(detail.doctor_reply.suggest_follow_up, '建议复查', '暂不需要复查')" tone="blue" />
        </div>
      </div>
    </PanelCard>

    <PanelCard v-else title="暂无病例" subtitle="当前筛选条件下没有可查看的问诊。">
      <EmptyState title="没有找到匹配问诊" copy="你可以清空筛选条件，或者回到工作台查看优先处理队列。" />
    </PanelCard>
  </section>
</template>
