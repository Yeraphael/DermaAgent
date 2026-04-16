<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app'
import { ref } from 'vue'

import { clearSession, ensureLogin, request } from '../../utils/api'

const profileData = ref<any>(null)
const notifications = ref<any[]>([])

async function loadProfile() {
  if (!ensureLogin()) return
  profileData.value = await request('/user/profile')
  const notice = await request<any>('/user/notifications?page=1&page_size=5')
  notifications.value = notice.list
}

function logout() {
  clearSession()
  uni.reLaunch({ url: '/pages/login/index' })
}

onShow(loadProfile)
</script>

<template>
  <view class="page-wrap safe-top">
    <view class="glass-card" style="padding: 34rpx;">
      <view style="display: flex; justify-content: space-between; align-items: center;">
        <view>
          <view class="section-title">{{ profileData?.profile?.real_name || '皮肤健康用户' }}</view>
          <view class="section-subtitle">{{ profileData?.account?.username }} · {{ profileData?.profile?.city || '未填写城市' }}</view>
        </view>
        <view class="chip">{{ profileData?.account?.phone }}</view>
      </view>

      <view class="stat-grid" style="margin-top: 24rpx;">
        <view class="stat-item">
          <view class="label">肤质</view>
          <view class="num" style="font-size: 34rpx;">{{ profileData?.health_profile?.skin_type || '未填' }}</view>
        </view>
        <view class="stat-item">
          <view class="label">敏感程度</view>
          <view class="num" style="font-size: 34rpx;">{{ profileData?.health_profile?.skin_sensitivity || '未填' }}</view>
        </view>
      </view>

      <view style="display: grid; gap: 16rpx; margin-top: 28rpx;">
        <view class="outline-btn" @click="uni.navigateTo({ url: '/pages/health/index' })">查看并编辑健康档案</view>
        <view class="outline-btn" @click="uni.switchTab({ url: '/pages/history/index' })">查看全部问诊记录</view>
        <view class="outline-btn" @click="logout">退出登录</view>
      </view>
    </view>

    <view style="height: 20rpx;" />

    <view class="glass-card" style="padding: 30rpx;">
      <view class="section-title" style="font-size: 34rpx;">近期通知</view>
      <view v-for="item in notifications" :key="item.notification_id" style="margin-top: 18rpx; padding: 24rpx; border-radius: 28rpx; background: rgba(9, 19, 31, 0.72);">
        <view style="font-size: 30rpx; font-weight: 600;">{{ item.title }}</view>
        <view class="section-subtitle">{{ item.content }}</view>
      </view>
    </view>
  </view>
</template>

