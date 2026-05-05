<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'

import EmptyState from '@/components/EmptyState.vue'
import PanelCard from '@/components/PanelCard.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import {
  archiveAdminConsultation,
  closeAdminConsultation,
  deleteAdminConsultation,
  fetchAdminConsultationDetail,
  fetchAdminConsultations,
  flagAdminConsultation,
  type ConsultationDetail,
} from '@/api/workspace'
import { cleanVisibleText, formatDateTime, riskLabel, riskTone, splitVisibleText, statusLabel, statusTone } from '@/utils/workspace'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const detailLoading = ref(false)
const selectedImageIndex = ref(0)
const filters = reactive({
  keyword: '',
  status: '',
  risk_level: '',
  archived_flag: null as number | null,
  abnormal_flag: null as number | null,
})

const list = ref<ConsultationDetail[]>([])
const detail = ref<ConsultationDetail | null>(null)
const manageForm = reactive({
  abnormal_note: '',
})

const selectedImage = computed(() => {
  const images = detail.value?.images || []
  return images[selectedImageIndex.value]?.file_url || images[0]?.file_url || ''
})

const aiDirections = computed(() => {
  return detail.value?.ai_result?.possible_conditions_list
    || splitVisibleText(detail.value?.ai_result?.possible_conditions)
})

async function loadList() {
  try {
    loading.value = true
    const result = await fetchAdminConsultations({
      page: 1,
      page_size: 50,
      keyword: filters.keyword || undefined,
      status: filters.status || undefined,
      risk_level: filters.risk_level || undefined,
      archived_flag: filters.archived_flag,
      abnormal_flag: filters.abnormal_flag,
    })
    list.value = result.list
    const routeId = Number(route.params.id)
    const matched = routeId ? result.list.find((item) => item.case_id === routeId) : null
    const targetId = matched?.case_id || result.list[0]?.case_id
    if (targetId && routeId !== targetId) {
      router.replace(`/admin/consultations/${targetId}`)
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
    detail.value = await fetchAdminConsultationDetail(caseId)
    manageForm.abnormal_note = detail.value.abnormal_note || ''
    selectedImageIndex.value = 0
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    detailLoading.value = false
  }
}

function selectCase(caseId: number) {
  router.replace(`/admin/consultations/${caseId}`)
}

async function handleFlag(abnormalFlag: number) {
  if (!detail.value) return
  try {
    await flagAdminConsultation(detail.value.case_id, {
      abnormal_flag: abnormalFlag,
      abnormal_note: manageForm.abnormal_note || undefined,
    })
    ElMessage.success('异常标记已更新。')
    await loadList()
    await loadDetail(detail.value.case_id)
  } catch (error) {
    ElMessage.error((error as Error).message)
  }
}

async function handleArchive(archivedFlag: number) {
  if (!detail.value) return
  try {
    await archiveAdminConsultation(detail.value.case_id, archivedFlag)
    ElMessage.success(archivedFlag ? '咨询已归档。' : '已取消归档。')
    await loadList()
    await loadDetail(detail.value.case_id)
  } catch (error) {
    ElMessage.error((error as Error).message)
  }
}

async function handleClose() {
  if (!detail.value) return
  try {
    await closeAdminConsultation(detail.value.case_id)
    ElMessage.success('咨询已关闭。')
    await loadList()
    await loadDetail(detail.value.case_id)
  } catch (error) {
    ElMessage.error((error as Error).message)
  }
}

async function handleDelete() {
  if (!detail.value) return
  try {
    await ElMessageBox.confirm('删除后该咨询将从默认列表中隐藏，但不会物理清除业务数据。是否继续？', '确认删除', {
      confirmButtonText: '继续删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteAdminConsultation(detail.value.case_id)
    ElMessage.success('咨询已删除。')
    await loadList()
  } catch (error) {
    if ((error as Error).message !== 'cancel') {
      ElMessage.error((error as Error).message)
    }
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
  <section class="two-panel-layout">
    <PanelCard title="咨询记录" subtitle="查看全平台问诊、AI 结果、医生回复与处理时间线。">
      <div class="filters-grid filters-grid--triple">
        <div class="form-field">
          <label>搜索病例、患者或症状</label>
          <input
            v-model="filters.keyword"
            class="ghost-input"
            placeholder="病例号、患者姓名、症状摘要"
            @keydown.enter.prevent="loadList"
          />
        </div>
        <div class="form-field">
          <label>状态</label>
          <el-select v-model="filters.status" clearable placeholder="全部状态">
            <el-option label="待医生处理" value="WAIT_DOCTOR" />
            <el-option label="医生已回复" value="DOCTOR_REPLIED" />
            <el-option label="AI 已完成" value="AI_DONE" />
            <el-option label="已关闭" value="CLOSED" />
          </el-select>
        </div>
        <div class="form-field">
          <label>风险等级</label>
          <el-select v-model="filters.risk_level" clearable placeholder="全部风险">
            <el-option label="低风险" value="LOW" />
            <el-option label="中风险" value="MEDIUM" />
            <el-option label="高风险" value="HIGH" />
          </el-select>
        </div>
      </div>

      <div class="filters-grid filters-grid--dual" style="margin-top: 14px;">
        <div class="form-field">
          <label>归档状态</label>
          <el-select v-model="filters.archived_flag" clearable placeholder="全部">
            <el-option label="未归档" :value="0" />
            <el-option label="已归档" :value="1" />
          </el-select>
        </div>
        <div class="form-field">
          <label>异常标记</label>
          <el-select v-model="filters.abnormal_flag" clearable placeholder="全部">
            <el-option label="正常" :value="0" />
            <el-option label="已标记异常" :value="1" />
          </el-select>
        </div>
      </div>

      <div class="action-row" style="margin-top: 14px;">
        <button type="button" class="primary-button" @click="loadList">刷新列表</button>
      </div>

      <div v-if="list.length" class="list-panel" style="margin-top: 18px;" v-loading="loading">
        <article
          v-for="item in list"
          :key="item.case_id"
          class="list-row"
          :class="{ 'is-active': detail?.case_id === item.case_id }"
          @click="selectCase(item.case_id)"
        >
          <div class="list-row__head">
            <div>
              <strong>{{ item.case_no }}</strong>
              <span>{{ item.patient?.profile?.real_name || item.patient?.account?.username || '患者' }} · {{ formatDateTime(item.submitted_at) }}</span>
            </div>
            <StatusBadge :label="statusLabel(item.status)" :tone="statusTone(item.status)" />
          </div>
          <p class="list-row__summary">{{ cleanVisibleText(item.summary_title, '待补充摘要') }}</p>
          <div class="action-row" style="margin-top: 12px;">
            <StatusBadge :label="riskLabel(item.risk_level)" :tone="riskTone(item.risk_level)" />
            <StatusBadge v-if="item.archived_flag" label="已归档" tone="slate" />
            <StatusBadge v-if="item.abnormal_flag" label="异常标记" tone="rose" />
          </div>
        </article>
      </div>
      <EmptyState v-else title="当前没有匹配咨询" copy="可以调整筛选条件，或等待新的问诊数据进入系统。" />
    </PanelCard>

    <PanelCard v-if="detail" title="咨询详情" subtitle="集中查看患者、AI、医生回复和时间线，并完成异常/归档处理。">
      <div v-loading="detailLoading">
        <div class="detail-card">
          <div class="detail-row">
            <div>
              <div class="tiny-label">病例编号</div>
              <p class="detail-title">{{ detail.case_no }}</p>
            </div>
            <div class="action-row">
              <StatusBadge :label="statusLabel(detail.status)" :tone="statusTone(detail.status)" />
              <StatusBadge :label="riskLabel(detail.risk_level)" :tone="riskTone(detail.risk_level)" />
            </div>
          </div>
          <p class="detail-copy">{{ cleanVisibleText(detail.summary_title, '待补充摘要') }}</p>
        </div>

        <div class="detail-card" style="margin-top: 18px;">
          <div class="tiny-label">患者与医生信息</div>
          <div class="key-value" style="margin-top: 10px;">
            <div class="key-value__row">
              <span>患者</span>
              <strong>{{ detail.patient?.profile?.real_name || detail.patient?.account?.username || '未命名患者' }}</strong>
            </div>
            <div class="key-value__row">
              <span>联系方式</span>
              <strong>{{ detail.patient?.account?.phone || '--' }}</strong>
            </div>
            <div class="key-value__row">
              <span>分配医生</span>
              <strong>{{ detail.doctor?.doctor_name || '待分配' }}</strong>
            </div>
            <div class="key-value__row">
              <span>提交时间</span>
              <strong>{{ formatDateTime(detail.submitted_at) }}</strong>
            </div>
          </div>
        </div>

        <div class="detail-card" style="margin-top: 18px;">
          <div class="tiny-label">症状与图片</div>
          <p class="detail-copy">{{ cleanVisibleText(detail.chief_complaint, '患者尚未补充完整症状描述。') }}</p>
          <div class="case-gallery" style="margin-top: 14px;">
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
        </div>

        <div class="detail-card" style="margin-top: 18px;">
          <div class="tiny-label">AI 分析结果</div>
          <p class="detail-copy">{{ cleanVisibleText(detail.ai_result?.image_observation, '系统正在整理图像观察结论。') }}</p>
          <div class="pill-stack" style="margin-top: 14px;">
            <StatusBadge v-for="item in aiDirections" :key="item" :label="item" tone="blue" />
          </div>
        </div>

        <div v-if="detail.doctor_reply" class="detail-card" style="margin-top: 18px;">
          <div class="tiny-label">医生回复</div>
          <p class="detail-copy">{{ cleanVisibleText(detail.doctor_reply.content, '暂无医生回复。') }}</p>
          <div class="pill-stack" style="margin-top: 14px;">
            <StatusBadge :label="detail.doctor_reply.doctor_name" tone="mint" />
            <StatusBadge :label="detail.doctor_reply.suggest_offline_visit ? '建议线下就医' : '暂不建议线下就医'" :tone="detail.doctor_reply.suggest_offline_visit ? 'amber' : 'blue'" />
          </div>
        </div>

        <div class="detail-card" style="margin-top: 18px;">
          <div class="tiny-label">处理时间线</div>
          <div v-if="detail.timeline.length" class="timeline-list">
            <article v-for="item in detail.timeline" :key="`${item.event}-${item.time}`" class="timeline-item">
              <div class="timeline-item__dot" />
              <div>
                <strong>{{ item.label }}</strong>
                <p>{{ cleanVisibleText(item.note, '已记录相关处理动作。') }}</p>
                <span>{{ item.time }}</span>
              </div>
            </article>
          </div>
          <EmptyState v-else title="暂无时间线" copy="关键处理动作写入后，会在这里展示完整时间线。" />
        </div>

        <div class="detail-card" style="margin-top: 18px;">
          <div class="form-field">
            <label>异常说明</label>
            <textarea v-model="manageForm.abnormal_note" class="ghost-textarea" placeholder="记录异常原因、处理意见或归档说明" />
          </div>
          <div class="action-row" style="margin-top: 14px;">
            <button type="button" class="soft-button" @click="handleFlag(detail.abnormal_flag ? 0 : 1)">
              {{ detail.abnormal_flag ? '取消异常标记' : '标记异常' }}
            </button>
            <button type="button" class="ghost-button" @click="handleArchive(detail.archived_flag ? 0 : 1)">
              {{ detail.archived_flag ? '取消归档' : '归档咨询' }}
            </button>
            <button type="button" class="primary-button" @click="handleClose">关闭咨询</button>
            <button type="button" class="ghost-button" @click="handleDelete">删除记录</button>
          </div>
        </div>
      </div>
    </PanelCard>

    <PanelCard v-else title="暂无咨询详情" subtitle="从左侧列表选择咨询后，可查看完整处理信息。">
      <EmptyState title="请选择咨询记录" copy="点击左侧咨询卡片，即可查看患者信息、AI 分析、医生回复与处理时间线。" />
    </PanelCard>
  </section>
</template>
