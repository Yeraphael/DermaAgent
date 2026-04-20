<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app'
import { ref } from 'vue'

import { getPortalConsultations, getPortalProfile, getPortalRiskLabel } from '../../shared/portal'
import { ensurePortalLogin } from '../../utils/miniPortal'

const profile = ref(getPortalProfile())
const cases = ref(getPortalConsultations().slice(0, 3))

function riskClass(risk: 'LOW' | 'MEDIUM' | 'HIGH') {
  return risk === 'HIGH' ? 'rose' : risk === 'MEDIUM' ? 'amber' : 'mint'
}

onShow(() => {
  if (!ensurePortalLogin()) return
  profile.value = getPortalProfile()
  cases.value = getPortalConsultations().slice(0, 3)
})
</script>

<template>
  <view class="page-wrap safe-top">
    <view class="mini-card" style="padding: 34rpx;">
      <view class="mini-eyebrow">健康档案</view>
      <view class="mini-title" style="margin-top: 12rpx;">你的皮肤健康档案</view>
      <view class="mini-subtitle">把最近的风险趋势、护理建议和历史问诊沉淀成连续可追踪的档案信息。</view>
    </view>

    <view class="mini-space" />

    <view class="mini-grid-2">
      <view class="mini-card" style="padding: 28rpx;">
        <view class="mini-card-title">风险趋势</view>
        <view v-for="item in profile.healthArchive.riskTrend" :key="item" class="mini-item" style="margin-top: 18rpx;">
          <view class="mini-item-title">趋势记录</view>
          <view class="mini-item-copy">{{ item }}</view>
        </view>
      </view>

      <view class="mini-card" style="padding: 28rpx;">
        <view class="mini-card-title">关键信息</view>
        <view class="mini-item" style="margin-top: 18rpx;">
          <view class="mini-item-title">皮肤类型</view>
          <view class="mini-item-copy">{{ profile.healthArchive.skinType }}</view>
        </view>
        <view class="mini-item" style="margin-top: 18rpx;">
          <view class="mini-item-title">最近医生</view>
          <view class="mini-item-copy">{{ profile.healthArchive.latestDoctor }}</view>
        </view>
      </view>
    </view>

    <view class="mini-space" />

    <view class="mini-card" style="padding: 30rpx;">
      <view class="mini-card-title">最近病例</view>
      <view v-for="item in cases" :key="item.caseId" class="mini-item" style="margin-top: 18rpx;">
        <view class="mini-item-title">{{ item.title }}</view>
        <view class="mini-item-copy">{{ item.description }}</view>
        <view class="mini-badge" :class="riskClass(item.riskLevel)" style="margin-top: 14rpx;">{{ getPortalRiskLabel(item.riskLevel) }}</view>
      </view>
    </view>
  </view>
</template>
