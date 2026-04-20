<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app'
import { ref } from 'vue'

import { getPortalDashboard, getPortalRiskLabel, getPortalStatusLabel } from '../../shared/portal'
import { ensurePortalLogin, openMiniPage, openMiniTab } from '../../utils/miniPortal'

const dashboard = ref(getPortalDashboard())

function tone(risk: 'LOW' | 'MEDIUM' | 'HIGH') {
  return risk === 'HIGH' ? 'rose' : risk === 'MEDIUM' ? 'amber' : 'mint'
}

function statusTone(status: string) {
  if (status === 'DOCTOR_REPLIED') return 'mint'
  if (status === 'WAIT_DOCTOR') return 'amber'
  return 'blue'
}

onShow(() => {
  if (!ensurePortalLogin()) return
  dashboard.value = getPortalDashboard()
})
</script>

<template>
  <view class="page-wrap safe-top">
    <view class="mini-card" style="padding: 34rpx;">
      <view class="mini-eyebrow">智能问诊入口</view>
      <view class="mini-title" style="margin-top: 12rpx;">你好，{{ dashboard.profile.real_name }}</view>
      <view class="mini-subtitle">今天也让皮肤状态更稳定一点。上传图片后，AI 会先给出观察结果和护理建议，需要时再接入医生回复。</view>

      <view class="mini-stat-grid" style="margin-top: 28rpx;">
        <view class="mini-metric"><text>问诊总量</text><text>{{ dashboard.summary.consultationTotal }}</text></view>
        <view class="mini-metric"><text>待医生回复</text><text>{{ dashboard.summary.waitingTotal }}</text></view>
        <view class="mini-metric"><text>医生已回复</text><text>{{ dashboard.summary.doctorReplyTotal }}</text></view>
        <view class="mini-metric"><text>未读通知</text><text>{{ dashboard.summary.unreadNotifications }}</text></view>
      </view>

      <view class="mini-grid-2" style="margin-top: 26rpx;">
        <view class="mini-primary" @click="openMiniTab('consultation')">开始问诊</view>
        <view class="mini-secondary" @click="openMiniPage('/pages/health/index')">健康档案</view>
      </view>
    </view>

    <view class="mini-space" />

    <view class="mini-card" style="padding: 30rpx;">
      <view class="mini-card-title">{{ dashboard.ongoingCase.title }}</view>
      <view class="mini-subtitle">{{ dashboard.ongoingCase.ai.observation }}</view>
      <view class="mini-actions" style="margin-top: 18rpx;">
        <view class="mini-badge" :class="tone(dashboard.ongoingCase.riskLevel)">{{ getPortalRiskLabel(dashboard.ongoingCase.riskLevel) }}</view>
        <view class="mini-badge slate" :class="statusTone(dashboard.ongoingCase.status)">{{ getPortalStatusLabel(dashboard.ongoingCase.status) }}</view>
      </view>
      <view class="mini-primary" style="margin-top: 22rpx;" @click="openMiniPage(`/pages/analysis/index?caseId=${dashboard.ongoingCase.caseId}`)">
        查看分析详情
      </view>
    </view>

    <view class="mini-space" />

    <view class="mini-card" style="padding: 30rpx;">
      <view class="mini-card-title">快速入口</view>
      <view class="mini-grid-2" style="margin-top: 20rpx;">
        <view
          v-for="item in dashboard.quickActions"
          :key="item.key"
          class="mini-item"
          @click="item.key === 'consultation' ? openMiniTab('consultation') : item.key === 'qa' ? openMiniTab('qa') : item.key === 'history' ? openMiniTab('history') : openMiniPage('/pages/analysis/index')"
        >
          <view class="mini-item-title">{{ item.label }}</view>
          <view class="mini-item-copy">{{ item.description }}</view>
        </view>
      </view>
    </view>

    <view class="mini-space" />

    <view class="mini-card" style="padding: 30rpx;">
      <view class="mini-card-title">最近记录</view>
      <view v-for="item in dashboard.recentCases" :key="item.caseId" class="mini-item" style="margin-top: 18rpx;" @click="openMiniPage(`/pages/analysis/index?caseId=${item.caseId}`)">
        <view class="mini-item-title">{{ item.title }}</view>
        <view class="mini-item-copy">{{ item.description }}</view>
        <view class="mini-actions" style="margin-top: 12rpx;">
          <view class="mini-badge" :class="tone(item.riskLevel)">{{ getPortalRiskLabel(item.riskLevel) }}</view>
          <view class="mini-badge slate">{{ getPortalStatusLabel(item.status) }}</view>
        </view>
      </view>
    </view>

    <MiniDock active="home" />
  </view>
</template>
