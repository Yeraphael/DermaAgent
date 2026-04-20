<script setup lang="ts">
import { onLoad, onShow } from '@dcloudio/uni-app'
import { ref } from 'vue'

import { buildVisualStyle, getPortalConsultation, getPortalConsultations, getPortalRiskLabel, getPortalStatusLabel } from '../../shared/portal'
import { ensurePortalLogin, openMiniPage } from '../../utils/miniPortal'

const detail = ref(getPortalConsultations()[0])
const caseId = ref<number | null>(null)

function riskClass(risk: 'LOW' | 'MEDIUM' | 'HIGH') {
  return risk === 'HIGH' ? 'rose' : risk === 'MEDIUM' ? 'amber' : 'mint'
}

function loadDetail() {
  detail.value = (caseId.value ? getPortalConsultation(caseId.value) : null) || getPortalConsultations()[0]
}

onLoad((options) => {
  caseId.value = options?.caseId ? Number(options.caseId) : null
  loadDetail()
})

onShow(() => {
  if (!ensurePortalLogin()) return
  loadDetail()
})
</script>

<template>
  <view v-if="detail" class="page-wrap safe-top">
    <view class="mini-card" style="padding: 32rpx;">
      <view class="mini-eyebrow">AI 分析结果</view>
      <view class="mini-title" style="margin-top: 12rpx;">{{ detail.title }}</view>
      <view class="mini-subtitle">{{ detail.caseNo }} · {{ detail.submittedAt }}</view>
      <view class="mini-actions" style="margin-top: 18rpx;">
        <view class="mini-badge" :class="riskClass(detail.riskLevel)">{{ getPortalRiskLabel(detail.riskLevel) }}</view>
        <view class="mini-badge slate">{{ getPortalStatusLabel(detail.status) }}</view>
      </view>
    </view>

    <view class="mini-space" />

    <view class="mini-card" style="padding: 30rpx;">
      <view class="mini-card-title">图片初步观察</view>
      <view class="mini-subtitle">{{ detail.ai.observation }}</view>
      <view class="mini-visuals" style="margin-top: 20rpx;">
        <view v-for="item in detail.visuals.slice(0, 3)" :key="item" class="mini-visual" :style="buildVisualStyle(item)" />
      </view>
    </view>

    <view class="mini-space" />

    <view class="mini-card" style="padding: 30rpx;">
      <view class="mini-card-title">可能相关方向</view>
      <view class="mini-progress" style="margin-top: 18rpx;">
        <view v-for="item in detail.ai.directions" :key="item.label" class="mini-progress-row">
          <text>{{ item.label }}</text>
          <view class="mini-progress-track"><view :style="{ width: `${item.value}%` }" /></view>
          <text>{{ item.value }}%</text>
        </view>
      </view>
    </view>

    <view class="mini-space" />

    <view class="mini-card" style="padding: 30rpx;">
      <view class="mini-card-title">护理建议</view>
      <view v-for="item in detail.ai.careAdvice" :key="item" class="mini-item" style="margin-top: 18rpx;">
        <view class="mini-item-title">护理建议</view>
        <view class="mini-item-copy">{{ item }}</view>
      </view>
      <view class="mini-item" style="margin-top: 18rpx;">
        <view class="mini-item-title">是否建议就医</view>
        <view class="mini-item-copy">{{ detail.ai.riskReason }}</view>
      </view>
    </view>

    <view class="mini-space" />

    <view class="mini-card" style="padding: 30rpx;">
      <view class="mini-card-title">医生回复与知识问答</view>
      <view v-if="detail.doctorReply" class="mini-item" style="margin-top: 18rpx;">
        <view class="mini-item-title">{{ detail.doctorReply.doctorName }}</view>
        <view class="mini-item-copy">{{ detail.doctorReply.content }}</view>
        <view class="mini-item-meta">{{ detail.doctorReply.repliedAt }}</view>
      </view>
      <view class="mini-secondary" style="margin-top: 20rpx;" @click="openMiniPage('/pages/qa/index')">进入知识问答</view>
      <view class="mini-subtitle" style="margin-top: 18rpx;">{{ detail.ai.disclaimer }}</view>
    </view>
  </view>
</template>
