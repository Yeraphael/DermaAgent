<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import ConfirmDialog from '../components/ConfirmDialog.vue'
import PageState from '../components/PageState.vue'
import RiskBadge from '../components/RiskBadge.vue'
import { deleteChatSession, fetchChatSessions, type ChatSessionSummary } from '../services/chat'
import { deleteConsultation, fetchMyConsultations, type ConsultationSummary } from '../services/consultation'
import { formatDateTime, getRiskLabel, getRiskTone, getStatusLabel, getStatusTone, sanitizeVisibleText } from '../utils/display'

type HistoryFilter = 'ALL' | 'CONSULTATION' | 'ANALYSIS' | 'DOCTOR' | 'QA'

type HistoryItem = {
  key: string
  source: 'consultation' | 'chat'
  sourceId: number
  type: Exclude<HistoryFilter, 'ALL'>
  title: string
  summary: string
  time: string
  statusLabel: string
  statusTone: 'blue' | 'violet' | 'mint' | 'amber' | 'rose' | 'slate'
  riskLabel?: string
  riskTone?: 'blue' | 'violet' | 'mint' | 'amber' | 'rose' | 'slate'
}

const router = useRouter()

const filter = ref<HistoryFilter>('ALL')
const loading = ref(false)
const errorMessage = ref('')
const consultations = ref<ConsultationSummary[]>([])
const chatSessions = ref<ChatSessionSummary[]>([])
const manageMode = ref(false)
const selectedKeys = ref<string[]>([])
const currentPage = ref(1)
const pageSize = 10
const deleteKeys = ref<string[]>([])
const deleteLoading = ref(false)
const swipedKey = ref('')
const touchStartX = ref(0)

const historyItems = computed<HistoryItem[]>(() => {
  const consultationItems = consultations.value.flatMap<HistoryItem>((item) => {
    const baseSummary = sanitizeVisibleText(item.ai_result?.image_observation || item.summary_title, '可点击查看病例详情。')
    const list: HistoryItem[] = [
      {
        key: `consultation:${item.case_id}`,
        source: 'consultation',
        sourceId: item.case_id,
        type: 'CONSULTATION',
        title: sanitizeVisibleText(item.summary_title, '图文问诊记录'),
        summary: baseSummary,
        time: item.submitted_at || '',
        statusLabel: getStatusLabel(item.status),
        statusTone: getStatusTone(item.status),
        riskLabel: getRiskLabel(item.risk_level),
        riskTone: getRiskTone(item.risk_level),
      },
      {
        key: `analysis:${item.case_id}`,
        source: 'consultation',
        sourceId: item.case_id,
        type: 'ANALYSIS',
        title: `${sanitizeVisibleText(item.summary_title, '病例记录')}智能分析`,
        summary: baseSummary,
        time: item.submitted_at || '',
        statusLabel: getStatusLabel(item.status),
        statusTone: getStatusTone(item.status),
        riskLabel: getRiskLabel(item.risk_level),
        riskTone: getRiskTone(item.risk_level),
      },
    ]

    if (item.doctor_reply?.content) {
      list.push({
        key: `doctor:${item.case_id}`,
        source: 'consultation',
        sourceId: item.case_id,
        type: 'DOCTOR',
        title: `关于${sanitizeVisibleText(item.summary_title, '该病例')}的医生回复`,
        summary: sanitizeVisibleText(item.doctor_reply.content),
        time: item.doctor_reply.created_at || item.submitted_at || '',
        statusLabel: '已回复',
        statusTone: 'mint',
        riskLabel: getRiskLabel(item.risk_level),
        riskTone: getRiskTone(item.risk_level),
      })
    }

    return list
  })

  const qaItems = chatSessions.value.map<HistoryItem>((item) => ({
    key: `chat:${item.session_id}`,
    source: 'chat',
    sourceId: item.session_id,
    type: 'QA',
    title: sanitizeVisibleText(item.title, '知识问答'),
    summary: sanitizeVisibleText(item.last_message, '继续提问，获取更多护理建议。'),
    time: item.updated_at,
    statusLabel: '已回复',
    statusTone: 'blue',
  }))

  return [...consultationItems, ...qaItems]
    .filter((item) => filter.value === 'ALL' || item.type === filter.value)
    .sort((left, right) => Date.parse(right.time || '') - Date.parse(left.time || ''))
})

const totalPages = computed(() => Math.max(1, Math.ceil(historyItems.value.length / pageSize)))
const pagedItems = computed(() => historyItems.value.slice((currentPage.value - 1) * pageSize, currentPage.value * pageSize))
const allPageSelected = computed(() => pagedItems.value.length > 0 && pagedItems.value.every((item) => selectedKeys.value.includes(item.key)))

async function loadData() {
  try {
    loading.value = true
    errorMessage.value = ''
    const [consultationResult, chatResult] = await Promise.all([
      fetchMyConsultations(1, 50),
      fetchChatSessions(),
    ])
    consultations.value = consultationResult.list
    chatSessions.value = chatResult.items || []
  } catch (error) {
    errorMessage.value = (error as Error).message || '加载历史记录失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

function toggleManageMode() {
  manageMode.value = !manageMode.value
  selectedKeys.value = []
  swipedKey.value = ''
}

function toggleKey(key: string) {
  if (selectedKeys.value.includes(key)) {
    selectedKeys.value = selectedKeys.value.filter((item) => item !== key)
    return
  }
  selectedKeys.value = [...selectedKeys.value, key]
}

function toggleSelectAllPage() {
  selectedKeys.value = allPageSelected.value ? [] : pagedItems.value.map((item) => item.key)
}

function openDetail(item: HistoryItem) {
  if (item.source === 'chat') {
    router.push({ path: '/qa', query: { session: String(item.sourceId) } })
    return
  }
  router.push(`/analysis/${item.sourceId}`)
}

function iconLabel(type: HistoryItem['type']) {
  if (type === 'CONSULTATION') return '图'
  if (type === 'ANALYSIS') return '析'
  if (type === 'DOCTOR') return '医'
  return '答'
}

function beginSwipe(event: TouchEvent) {
  touchStartX.value = event.changedTouches[0]?.clientX || 0
}

function endSwipe(event: TouchEvent, key: string) {
  const delta = (event.changedTouches[0]?.clientX || 0) - touchStartX.value
  if (delta < -40) {
    swipedKey.value = key
  } else if (delta > 24 && swipedKey.value === key) {
    swipedKey.value = ''
  }
}

function requestDelete(keys: string[]) {
  deleteKeys.value = keys
}

async function confirmDelete() {
  const consultationIds = [...new Set(deleteKeys.value.filter((key) => key.startsWith('consultation:') || key.startsWith('analysis:') || key.startsWith('doctor:')).map((key) => Number(key.split(':')[1])))]
  const chatIds = [...new Set(deleteKeys.value.filter((key) => key.startsWith('chat:')).map((key) => Number(key.split(':')[1])))]

  const backupConsultations = [...consultations.value]
  const backupChats = [...chatSessions.value]
  consultations.value = consultations.value.filter((item) => !consultationIds.includes(item.case_id))
  chatSessions.value = chatSessions.value.filter((item) => !chatIds.includes(item.session_id))
  selectedKeys.value = []
  manageMode.value = false
  swipedKey.value = ''

  try {
    deleteLoading.value = true
    await Promise.all([
      ...consultationIds.map((id) => deleteConsultation(id)),
      ...chatIds.map((id) => deleteChatSession(id)),
    ])
    deleteKeys.value = []
    window.alert('删除成功')
  } catch (error) {
    consultations.value = backupConsultations
    chatSessions.value = backupChats
    window.alert((error as Error).message || '删除失败，请稍后重试')
  } finally {
    deleteLoading.value = false
  }
}

watch(filter, () => {
  currentPage.value = 1
  selectedKeys.value = []
  swipedKey.value = ''
})

watch(totalPages, (value) => {
  currentPage.value = Math.min(currentPage.value, value)
})

onMounted(() => {
  void loadData()
})
</script>

<template>
  <section class="page-stack history-page">
    <article class="surface-card">
      <div class="section-head">
        <div>
          <p class="section-eyebrow">历史记录</p>
          <h1 class="section-title">在这里可以查看您过往的问诊、分析、医生回复及问答记录，便于跟踪健康变化。</h1>
        </div>
        <button type="button" class="secondary-button" @click="toggleManageMode">
          {{ manageMode ? '取消管理' : '批量管理' }}
        </button>
      </div>

      <div class="history-tabs">
        <button type="button" :class="{ 'is-active': filter === 'ALL' }" @click="filter = 'ALL'">全部</button>
        <button type="button" :class="{ 'is-active': filter === 'CONSULTATION' }" @click="filter = 'CONSULTATION'">图文问诊</button>
        <button type="button" :class="{ 'is-active': filter === 'ANALYSIS' }" @click="filter = 'ANALYSIS'">智能分析</button>
        <button type="button" :class="{ 'is-active': filter === 'DOCTOR' }" @click="filter = 'DOCTOR'">医生回复</button>
        <button type="button" :class="{ 'is-active': filter === 'QA' }" @click="filter = 'QA'">知识问答</button>
      </div>
    </article>

    <PageState
      v-if="loading"
      title="正在加载历史记录"
      description="请稍候，我们正在同步您的问诊与问答内容。"
    />

    <PageState
      v-else-if="errorMessage"
      tone="error"
      title="历史记录加载失败"
      :description="errorMessage"
      action-text="重新加载"
      @action="loadData"
    />

    <PageState
      v-else-if="!historyItems.length"
      tone="empty"
      title="当前还没有历史记录"
      description="发起问诊、查看分析或进行知识问答后，相关记录会同步展示在这里。"
      action-text="去图文问诊"
      @action="router.push('/consultation')"
    />

    <template v-else>
      <article v-if="manageMode" class="surface-card history-manage">
        <button type="button" class="text-button" @click="toggleSelectAllPage">
          {{ allPageSelected ? '取消全选' : '全选当前页' }}
        </button>
        <span>已选 {{ selectedKeys.length }} 项</span>
        <button type="button" class="text-button history-manage__danger" :disabled="!selectedKeys.length" @click="requestDelete(selectedKeys)">
          删除所选
        </button>
      </article>

      <div class="history-list">
        <article
          v-for="item in pagedItems"
          :key="item.key"
          class="history-swipe"
          :class="{ 'is-open': swipedKey === item.key }"
          @touchstart="beginSwipe"
          @touchend="endSwipe($event, item.key)"
        >
          <button type="button" class="history-swipe__action" @click="requestDelete([item.key])">删除</button>

          <div class="surface-card history-card">
            <label v-if="manageMode" class="history-card__checkbox">
              <input :checked="selectedKeys.includes(item.key)" type="checkbox" @change="toggleKey(item.key)" />
            </label>

            <div class="history-card__icon">{{ iconLabel(item.type) }}</div>

            <button type="button" class="history-card__main" @click="openDetail(item)">
              <div class="history-card__meta">
                <RiskBadge
                  :label="item.type === 'CONSULTATION' ? '图文问诊' : item.type === 'ANALYSIS' ? '智能分析' : item.type === 'DOCTOR' ? '医生回复' : '知识问答'"
                  :tone="item.type === 'CONSULTATION' ? 'blue' : item.type === 'ANALYSIS' ? 'violet' : item.type === 'DOCTOR' ? 'mint' : 'amber'"
                />
                <span>{{ formatDateTime(item.time) }}</span>
              </div>
              <strong>{{ item.title }}</strong>
              <p>{{ item.summary }}</p>
            </button>

            <div class="history-card__status">
              <RiskBadge :label="item.statusLabel" :tone="item.statusTone" />
              <RiskBadge v-if="item.riskLabel" :label="item.riskLabel" :tone="item.riskTone" />
            </div>

            <div class="history-card__actions">
              <button type="button" class="secondary-button" @click="openDetail(item)">查看详情</button>
              <button type="button" class="secondary-button" @click="requestDelete([item.key])">删除</button>
            </div>
          </div>
        </article>
      </div>

      <article class="surface-card history-pager">
        <button type="button" class="secondary-button" :disabled="currentPage <= 1" @click="currentPage -= 1">上一页</button>
        <span>第 {{ currentPage }} / {{ totalPages }} 页</span>
        <button type="button" class="secondary-button" :disabled="currentPage >= totalPages" @click="currentPage += 1">下一页</button>
      </article>

      <article v-if="manageMode" class="surface-card history-mobile-bar">
        <button type="button" class="text-button" @click="toggleSelectAllPage">
          {{ allPageSelected ? '取消全选' : '全选当前页' }}
        </button>
        <span>已选 {{ selectedKeys.length }} 项</span>
        <button type="button" class="text-button history-manage__danger" :disabled="!selectedKeys.length" @click="requestDelete(selectedKeys)">
          删除所选
        </button>
      </article>
    </template>

    <ConfirmDialog
      :visible="deleteKeys.length > 0"
      :title="deleteKeys.length > 1 ? '确认删除选中的记录？' : '确认删除该记录？'"
      description="删除后无法恢复。"
      confirm-text="确认删除"
      cancel-text="取消"
      :danger="true"
      :loading="deleteLoading"
      @cancel="deleteKeys = []"
      @confirm="confirmDelete"
    />
  </section>
</template>

<style scoped>
.history-page {
  padding-bottom: 96px;
}

.history-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
}

.history-tabs button {
  min-height: 42px;
  padding: 0 16px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.96);
  color: var(--text-sub);
  font-weight: 700;
}

.history-tabs button.is-active {
  border-color: rgba(47, 125, 255, 0.48);
  background: rgba(47, 125, 255, 0.1);
  color: var(--blue);
}

.history-manage,
.history-pager,
.history-mobile-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.history-manage__danger {
  color: var(--rose);
}

.history-list {
  display: grid;
  gap: 14px;
}

.history-swipe {
  position: relative;
  overflow: hidden;
  border-radius: 24px;
}

.history-swipe__action {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 92px;
  border: 0;
  color: #ffffff;
  background: linear-gradient(135deg, #ff7c89 0%, #ef5b6d 100%);
}

.history-card {
  display: grid;
  grid-template-columns: auto auto minmax(0, 1fr) auto auto;
  gap: 14px;
  align-items: center;
  transition: transform 0.2s ease;
}

.history-card__icon {
  display: inline-grid;
  place-items: center;
  width: 48px;
  height: 48px;
  border-radius: 16px;
  color: #ffffff;
  font-weight: 700;
  background: var(--gradient-main);
}

.history-card__main {
  min-height: auto;
  padding: 0;
  border: 0;
  background: transparent;
  text-align: left;
}

.history-card__meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.history-card__meta span {
  color: var(--text-faint);
  font-size: 12px;
}

.history-card__main strong {
  display: block;
  margin-top: 10px;
  color: var(--text-strong);
  font-size: 16px;
}

.history-card__main p {
  margin: 8px 0 0;
  color: var(--text-sub);
  font-size: 14px;
  line-height: 1.8;
}

.history-card__status,
.history-card__actions {
  display: grid;
  gap: 10px;
}

.history-mobile-bar {
  display: none;
  position: fixed;
  left: 12px;
  right: 12px;
  bottom: 12px;
  z-index: 30;
}

@media (max-width: 980px) {
  .history-card {
    grid-template-columns: auto minmax(0, 1fr);
    align-items: start;
  }

  .history-card__checkbox,
  .history-card__status,
  .history-card__actions {
    grid-column: 2;
  }

  .history-card__actions {
    display: none;
  }

  .history-swipe.is-open .history-card {
    transform: translateX(-92px);
  }

  .history-pager {
    justify-content: center;
  }

  .history-mobile-bar {
    display: flex;
  }
}
</style>
