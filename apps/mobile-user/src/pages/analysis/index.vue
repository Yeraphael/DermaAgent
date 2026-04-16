<script setup lang="ts">
import { onLoad } from '@dcloudio/uni-app'
import { ref } from 'vue'

import { ensureLogin, request } from '../../utils/api'

const detail = ref<any>(null)

async function loadDetail(caseId: number) {
  if (!ensureLogin()) return
  detail.value = await request(`/consultations/${caseId}`)
}

function goHistory() {
  uni.switchTab({ url: '/pages/history/index' })
}

onLoad((options) => {
  if (options?.caseId) {
    loadDetail(Number(options.caseId))
  }
})
</script>

<template>
  <view class="page-wrap safe-top">
    <view class="glass-card" style="padding: 32rpx;">
      <view class="section-title">AI 分析结果</view>
      <view class="section-subtitle">{{ detail?.case_no }} · {{ detail?.summary_title }}</view>

      <view style="margin-top: 24rpx; display: flex; justify-content: space-between; gap: 14rpx;">
        <view class="chip">{{ detail?.status }}</view>
        <view class="chip">风险 {{ detail?.risk_level || '-' }}</view>
      </view>

      <view class="stat-grid" style="margin-top: 24rpx;">
        <view class="stat-item">
          <view class="label">瘙痒</view>
          <view class="num">{{ detail?.itch_level || 0 }}</view>
        </view>
        <view class="stat-item">
          <view class="label">疼痛</view>
          <view class="num">{{ detail?.pain_level || 0 }}</view>
        </view>
      </view>

      <view style="margin-top: 24rpx; display: grid; gap: 16rpx;">
        <view class="glass-card" style="padding: 26rpx;">
          <view class="label">图像观察</view>
          <view style="margin-top: 12rpx; font-size: 28rpx; line-height: 1.8;">{{ detail?.ai_result?.image_observation }}</view>
        </view>
        <view class="glass-card" style="padding: 26rpx;">
          <view class="label">可能方向</view>
          <view style="margin-top: 12rpx; font-size: 28rpx; line-height: 1.8;">{{ detail?.ai_result?.possible_conditions }}</view>
        </view>
        <view class="glass-card" style="padding: 26rpx;">
          <view class="label">护理建议</view>
          <view style="margin-top: 12rpx; font-size: 28rpx; line-height: 1.8;">{{ detail?.ai_result?.care_advice }}</view>
        </view>
        <view class="glass-card" style="padding: 26rpx;">
          <view class="label">就医提醒</view>
          <view style="margin-top: 12rpx; font-size: 28rpx; line-height: 1.8; color: #ffb0b0;">{{ detail?.ai_result?.high_risk_alert }}</view>
          <view class="section-subtitle">{{ detail?.ai_result?.disclaimer }}</view>
        </view>
      </view>

      <view v-if="detail?.doctor_reply" style="margin-top: 24rpx;" class="glass-card">
        <view style="padding: 28rpx;">
          <view class="label">医生回复</view>
          <view style="margin-top: 10rpx; font-size: 30rpx; font-weight: 700;">{{ detail.doctor_reply.doctor_name }}</view>
          <view style="margin-top: 14rpx; line-height: 1.8;">{{ detail.doctor_reply.content }}</view>
        </view>
      </view>

      <view style="display: flex; gap: 16rpx; margin-top: 28rpx;">
        <view class="outline-btn" style="flex: 1;" @click="goHistory">查看历史记录</view>
        <view class="primary-btn" style="flex: 1;" @click="uni.switchTab({ url: '/pages/qa/index' })">继续知识问答</view>
      </view>
    </view>
  </view>
</template>
