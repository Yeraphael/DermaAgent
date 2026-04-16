<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app'
import { ref } from 'vue'

import { ensureLogin, request } from '../../utils/api'

const list = ref<any[]>([])

async function loadHistory() {
  if (!ensureLogin()) return
  const data = await request<any>('/consultations/my?page=1&page_size=30')
  list.value = data.list
}

function openCase(caseId: number) {
  uni.navigateTo({ url: `/pages/analysis/index?caseId=${caseId}` })
}

onShow(loadHistory)
</script>

<template>
  <view class="page-wrap safe-top">
    <view class="glass-card" style="padding: 30rpx;">
      <view class="section-title">问诊历史</view>
      <view class="section-subtitle">这里汇总你所有图文问诊记录、AI 分析状态和医生回复情况。</view>

      <view v-for="item in list" :key="item.case_id" style="margin-top: 20rpx; padding: 26rpx; border-radius: 30rpx; background: rgba(9, 19, 31, 0.72);" @click="openCase(item.case_id)">
        <view style="display: flex; justify-content: space-between; gap: 12rpx;">
          <view>
            <view style="font-size: 30rpx; font-weight: 700;">{{ item.summary_title }}</view>
            <view class="section-subtitle">{{ item.case_no }} · {{ item.submitted_at }}</view>
          </view>
          <view class="chip">{{ item.status }}</view>
        </view>
        <view style="margin-top: 16rpx; display: flex; gap: 16rpx;">
          <view class="chip">风险 {{ item.risk_level || '-' }}</view>
          <view class="chip">{{ item.doctor_reply ? '医生已回复' : '等待医生协同' }}</view>
        </view>
      </view>
    </view>
  </view>
</template>

