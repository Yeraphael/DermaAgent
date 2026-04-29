<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app'
import { computed, ref } from 'vue'

import { deleteChatSession, fetchChatSessions } from '../../services/chat'
import { deleteConsultation, fetchMyConsultations } from '../../services/consultation'
import { formatDateTime, getRiskLabel, getStatusLabel, sanitizeVisibleText } from '../../utils/display'
import { ensureLogin } from '../../utils/api'

type TabKey = 'ALL' | 'CONSULTATION' | 'ANALYSIS' | 'DOCTOR' | 'QA'

const tab = ref<TabKey>('ALL')
const consultations = ref<any[]>([])
const sessions = ref<any[]>([])
const loading = ref(false)
const manageMode = ref(false)
const selectedKeys = ref<string[]>([])

const items = computed(() => {
  const consultationItems = consultations.value.flatMap((item) => {
    const base = [
      {
        key: `consultation:${item.case_id}`,
        type: 'CONSULTATION',
        title: sanitizeVisibleText(item.summary_title, '图文问诊记录'),
        time: item.submitted_at,
        summary: sanitizeVisibleText(item.ai_result?.image_observation, '可点击查看病例详情。'),
        status: getStatusLabel(item.status),
        risk: getRiskLabel(item.risk_level),
        caseId: item.case_id,
      },
      {
        key: `analysis:${item.case_id}`,
        type: 'ANALYSIS',
        title: `${sanitizeVisibleText(item.summary_title, '病例记录')}智能分析`,
        time: item.submitted_at,
        summary: sanitizeVisibleText(item.ai_result?.image_observation, '可点击查看分析详情。'),
        status: getStatusLabel(item.status),
        risk: getRiskLabel(item.risk_level),
        caseId: item.case_id,
      },
    ]

    if (item.doctor_reply?.content) {
      base.push({
        key: `doctor:${item.case_id}`,
        type: 'DOCTOR',
        title: `关于${sanitizeVisibleText(item.summary_title, '该病例')}的医生回复`,
        time: item.doctor_reply.created_at || item.submitted_at,
        summary: sanitizeVisibleText(item.doctor_reply.content),
        status: '已回复',
        risk: getRiskLabel(item.risk_level),
        caseId: item.case_id,
      })
    }

    return base
  })

  const qaItems = sessions.value.map((item) => ({
    key: `chat:${item.session_id}`,
    type: 'QA',
    title: sanitizeVisibleText(item.title, '知识问答'),
    time: item.updated_at,
    summary: sanitizeVisibleText(item.last_message, '继续提问，获取更多护理建议。'),
    status: '已回复',
    risk: '',
    sessionId: item.session_id,
  }))

  return [...consultationItems, ...qaItems]
    .filter((item) => tab.value === 'ALL' || item.type === tab.value)
    .sort((left, right) => Date.parse(right.time || '') - Date.parse(left.time || ''))
})

function toggleSelection(key: string) {
  if (selectedKeys.value.includes(key)) {
    selectedKeys.value = selectedKeys.value.filter((item) => item !== key)
    return
  }
  selectedKeys.value = [...selectedKeys.value, key]
}

async function loadData() {
  if (!ensureLogin()) return

  try {
    loading.value = true
    const [consultationResult, sessionResult] = await Promise.all([
      fetchMyConsultations(1, 50),
      fetchChatSessions(),
    ])
    consultations.value = consultationResult.list
    sessions.value = sessionResult.items || []
  } finally {
    loading.value = false
  }
}

function openDetail(item: any) {
  if (item.sessionId) {
    uni.setStorageSync('qa_target_session', item.sessionId)
    uni.switchTab({ url: '/pages/qa/index' })
    return
  }

  uni.navigateTo({ url: `/pages/analysis/index?caseId=${item.caseId}` })
}

function requestDelete(keys: string[]) {
  const content = keys.length > 1 ? '确认删除选中的记录？删除后无法恢复。' : '确认删除该记录？删除后无法恢复。'
  uni.showModal({
    title: '删除确认',
    content,
    success: async (res) => {
      if (!res.confirm) return

      const consultationIds = [...new Set(keys.filter((key) => key.startsWith('consultation:') || key.startsWith('analysis:') || key.startsWith('doctor:')).map((key) => Number(key.split(':')[1])))]
      const chatIds = [...new Set(keys.filter((key) => key.startsWith('chat:')).map((key) => Number(key.split(':')[1])))]

      const backupConsultations = [...consultations.value]
      const backupSessions = [...sessions.value]
      consultations.value = consultations.value.filter((item) => !consultationIds.includes(item.case_id))
      sessions.value = sessions.value.filter((item) => !chatIds.includes(item.session_id))
      selectedKeys.value = []
      manageMode.value = false

      try {
        await Promise.all([
          ...consultationIds.map((id) => deleteConsultation(id)),
          ...chatIds.map((id) => deleteChatSession(id)),
        ])
        uni.showToast({ title: '删除成功', icon: 'success' })
      } catch (error: any) {
        consultations.value = backupConsultations
        sessions.value = backupSessions
        uni.showToast({ title: error.message || '删除失败，请稍后重试', icon: 'none' })
      }
    },
  })
}

onShow(() => {
  void loadData()
})
</script>

<template>
  <view class="page-wrap safe-top history-page">
    <view class="surface-card history-header">
      <view class="section-title">历史记录</view>
      <view class="section-subtitle">在这里可以查看您过往的问诊、分析、医生回复及问答记录，便于跟踪健康变化。</view>
      <view class="chip-row history-tabs">
        <view class="chip" :class="{ active: tab === 'ALL' }" @click="tab = 'ALL'">全部</view>
        <view class="chip" :class="{ active: tab === 'CONSULTATION' }" @click="tab = 'CONSULTATION'">图文问诊</view>
        <view class="chip" :class="{ active: tab === 'ANALYSIS' }" @click="tab = 'ANALYSIS'">智能分析</view>
        <view class="chip" :class="{ active: tab === 'DOCTOR' }" @click="tab = 'DOCTOR'">医生回复</view>
        <view class="chip" :class="{ active: tab === 'QA' }" @click="tab = 'QA'">知识问答</view>
      </view>
      <view class="secondary-btn" style="margin-top: 18rpx;" @click="manageMode = !manageMode; selectedKeys = []">
        {{ manageMode ? '取消管理' : '批量管理' }}
      </view>
    </view>

    <view v-if="manageMode" class="surface-card history-batch">
      <view class="text-btn" @click="selectedKeys = selectedKeys.length === items.length ? [] : items.map((item) => item.key)">
        {{ selectedKeys.length === items.length && items.length ? '取消全选' : '全选' }}
      </view>
      <view class="label">已选 {{ selectedKeys.length }} 项</view>
      <view class="text-btn history-batch__danger" @click="selectedKeys.length && requestDelete(selectedKeys)">删除所选</view>
    </view>

    <view v-if="loading" class="surface-card history-card">
      <view class="section-subtitle" style="margin-top: 0;">正在加载历史记录...</view>
    </view>

    <view v-else-if="!items.length" class="surface-card history-card">
      <view class="section-subtitle" style="margin-top: 0;">当前还没有相关记录。</view>
    </view>

    <view v-else class="history-list">
      <view v-for="item in items" :key="item.key" class="surface-card history-card">
        <view class="history-card__top">
          <view v-if="manageMode" class="history-card__check" @click="toggleSelection(item.key)">
            {{ selectedKeys.includes(item.key) ? '✓' : '' }}
          </view>
          <view class="history-card__main" @click="openDetail(item)">
            <view class="history-card__title">{{ item.title }}</view>
            <view class="history-card__time">{{ formatDateTime(item.time) }}</view>
            <view class="section-subtitle">{{ item.summary }}</view>
          </view>
        </view>

        <view class="chip-row" style="margin-top: 16rpx;">
          <view class="chip">{{ item.type === 'CONSULTATION' ? '图文问诊' : item.type === 'ANALYSIS' ? '智能分析' : item.type === 'DOCTOR' ? '医生回复' : '知识问答' }}</view>
          <view class="status-chip mint">{{ item.status }}</view>
          <view v-if="item.risk" class="status-chip amber">{{ item.risk }}</view>
        </view>

        <view class="history-card__actions">
          <view class="secondary-btn" @click="openDetail(item)">查看详情</view>
          <view class="secondary-btn" @click="requestDelete([item.key])">删除</view>
        </view>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.history-page {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.history-header,
.history-batch,
.history-card {
  padding: 28rpx;
}

.history-tabs .chip.active {
  background: rgba(47, 125, 255, 0.16);
}

.history-batch {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.history-batch__danger {
  color: #ef5b6d;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.history-card__top {
  display: flex;
  gap: 14rpx;
}

.history-card__check {
  width: 44rpx;
  height: 44rpx;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(47, 125, 255, 0.46);
  color: #2f7dff;
}

.history-card__main {
  flex: 1;
}

.history-card__title {
  color: #15326a;
  font-size: 30rpx;
  font-weight: 700;
}

.history-card__time {
  margin-top: 8rpx;
  color: #7a8fb3;
  font-size: 22rpx;
}

.history-card__actions {
  display: flex;
  gap: 12rpx;
  margin-top: 18rpx;
}

.history-card__actions .secondary-btn {
  flex: 1;
}
</style>
