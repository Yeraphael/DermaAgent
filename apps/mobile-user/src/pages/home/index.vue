<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app'
import { ref } from 'vue'

import { ensureLogin, getSession, request } from '../../utils/api'

const dashboard = ref<any>(null)
const announcements = ref<any[]>([])

async function loadData() {
  if (!ensureLogin()) return
  dashboard.value = await request('/user/dashboard')
  announcements.value = await request('/announcements')
}

function goConsultation() {
  uni.switchTab({ url: '/pages/consultation/index' })
}

function goQA() {
  uni.switchTab({ url: '/pages/qa/index' })
}

function goHealth() {
  uni.navigateTo({ url: '/pages/health/index' })
}

function openCase(caseId: number) {
  uni.navigateTo({ url: `/pages/analysis/index?caseId=${caseId}` })
}

onShow(loadData)
</script>

<template>
  <view class="page-wrap safe-top">
    <view class="glass-card" style="padding: 36rpx;">
      <view style="display: flex; justify-content: space-between; align-items: flex-start; gap: 18rpx;">
        <view>
          <view class="label">欢迎回来</view>
          <view class="section-title">{{ dashboard?.profile?.real_name || getSession()?.profile?.real_name || '皮肤健康用户' }}</view>
          <view class="section-subtitle">今天也把皮肤状态照顾得更稳定一些。</view>
        </view>
        <view class="chip">AI + 医生双协同</view>
      </view>

      <view class="stat-grid" style="margin-top: 28rpx;">
        <view class="stat-item">
          <view class="label">问诊总量</view>
          <view class="num">{{ dashboard?.summary?.consultation_total || 0 }}</view>
        </view>
        <view class="stat-item">
          <view class="label">待处理</view>
          <view class="num">{{ dashboard?.summary?.waiting_total || 0 }}</view>
        </view>
        <view class="stat-item">
          <view class="label">医生已回复</view>
          <view class="num">{{ dashboard?.summary?.doctor_replied_total || 0 }}</view>
        </view>
        <view class="stat-item">
          <view class="label">未读通知</view>
          <view class="num">{{ dashboard?.summary?.unread_notifications || 0 }}</view>
        </view>
      </view>

      <view style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16rpx; margin-top: 28rpx;">
        <view class="outline-btn" @click="goConsultation">发起图文问诊</view>
        <view class="outline-btn" @click="goQA">知识问答</view>
        <view class="outline-btn" @click="goHealth">健康档案</view>
      </view>
    </view>

    <view style="height: 20rpx;" />

    <view v-if="dashboard?.current_focus" class="glass-card" style="padding: 32rpx;">
      <view class="label">当前关注</view>
      <view style="margin-top: 14rpx; display: flex; justify-content: space-between; gap: 18rpx; align-items: center;">
        <view>
          <view style="font-size: 34rpx; font-weight: 700;">{{ dashboard.current_focus.summary_title }}</view>
          <view class="section-subtitle">{{ dashboard.current_focus.case_no }} · {{ dashboard.current_focus.status }} · {{ dashboard.current_focus.risk_level }}</view>
        </view>
        <view class="chip" @click="openCase(dashboard.current_focus.case_id)">查看结果</view>
      </view>
    </view>

    <view style="height: 20rpx;" />

    <view class="glass-card" style="padding: 30rpx;">
      <view class="section-title" style="font-size: 34rpx;">最近问诊</view>
      <view v-for="item in dashboard?.recent_cases || []" :key="item.case_id" style="margin-top: 20rpx; padding: 24rpx; border-radius: 28rpx; background: rgba(9, 19, 31, 0.7);" @click="openCase(item.case_id)">
        <view style="display: flex; justify-content: space-between; gap: 12rpx;">
          <view style="font-size: 30rpx; font-weight: 600;">{{ item.summary_title }}</view>
          <view class="chip">{{ item.status }}</view>
        </view>
        <view class="section-subtitle">{{ item.case_no }} · 风险 {{ item.risk_level || '-' }} · {{ item.submitted_at }}</view>
      </view>
    </view>

    <view style="height: 20rpx;" />

    <view class="glass-card" style="padding: 30rpx;">
      <view class="section-title" style="font-size: 34rpx;">平台公告</view>
      <view v-for="item in announcements.slice(0, 3)" :key="item.announcement_id" style="margin-top: 18rpx; padding-bottom: 18rpx; border-bottom: 1px solid rgba(184, 220, 255, 0.08);">
        <view style="font-size: 30rpx; font-weight: 600;">{{ item.title }}</view>
        <view class="section-subtitle">{{ item.content }}</view>
      </view>
    </view>
  </view>
</template>
