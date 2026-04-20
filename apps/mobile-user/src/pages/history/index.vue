<script setup lang="ts">
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

import { getPortalConsultations, getPortalNotifications, getPortalRiskLabel, getPortalStatusLabel } from '../../shared/portal'
import { ensurePortalLogin, openMiniPage } from '../../utils/miniPortal'

const filter = ref<'ALL' | 'AI' | 'DOCTOR' | 'SYSTEM'>('ALL')

const timeline = computed(() => {
  const consultations = getPortalConsultations().map((item) => ({
    id: item.caseId,
    type: item.status === 'DOCTOR_REPLIED' ? 'DOCTOR' : 'AI',
    title: item.title,
    summary: `${getPortalStatusLabel(item.status)} · ${getPortalRiskLabel(item.riskLevel)}`,
    copy: item.ai.observation,
    caseId: item.caseId,
  }))

  const notifications = getPortalNotifications().map((item) => ({
    id: item.id,
    type: item.category,
    title: item.title,
    summary: item.time,
    copy: item.summary,
    caseId: item.linkedCaseId,
  }))

  return [...consultations, ...notifications].filter((item) => filter.value === 'ALL' || item.type === filter.value)
})

onShow(() => {
  ensurePortalLogin()
})
</script>

<template>
  <view class="page-wrap safe-top">
    <view class="mini-card" style="padding: 32rpx;">
      <view class="mini-eyebrow">历史记录与通知</view>
      <view class="mini-title" style="margin-top: 12rpx;">所有关键节点都在这里</view>
      <view class="mini-subtitle">AI 分析、医生回复和系统通知统一以轻量时间线卡片呈现。</view>
      <view class="mini-segment" style="margin-top: 24rpx;">
        <view class="mini-segment-item" :class="{ active: filter === 'ALL' }" @click="filter = 'ALL'">全部</view>
        <view class="mini-segment-item" :class="{ active: filter === 'AI' }" @click="filter = 'AI'">AI</view>
        <view class="mini-segment-item" :class="{ active: filter === 'DOCTOR' }" @click="filter = 'DOCTOR'">医生</view>
        <view class="mini-segment-item" :class="{ active: filter === 'SYSTEM' }" @click="filter = 'SYSTEM'">系统</view>
      </view>
    </view>

    <view class="mini-space" />

    <view v-for="item in timeline" :key="`${item.type}-${item.id}`" class="mini-card compact" style="padding: 26rpx;" @click="item.caseId ? openMiniPage(`/pages/analysis/index?caseId=${item.caseId}`) : undefined">
      <view class="mini-item-title">{{ item.title }}</view>
      <view class="mini-item-copy">{{ item.copy }}</view>
      <view class="mini-item-meta">{{ item.type }} · {{ item.summary }}</view>
    </view>

    <MiniDock active="history" />
  </view>
</template>
