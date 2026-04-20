<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app'
import { ref } from 'vue'

import { getPortalProfile } from '../../shared/portal'
import { ensurePortalLogin, openMiniPage } from '../../utils/miniPortal'

const data = ref(getPortalProfile())

onShow(() => {
  if (!ensurePortalLogin()) return
  data.value = getPortalProfile()
})
</script>

<template>
  <view class="page-wrap safe-top">
    <view class="mini-card" style="padding: 34rpx;">
      <view class="mini-eyebrow">个人中心</view>
      <view class="mini-title" style="margin-top: 12rpx;">{{ data.profile.real_name }}</view>
      <view class="mini-subtitle">{{ data.profile.city }} · {{ data.profile.age }} 岁 · {{ data.profile.skin_type }}</view>
      <view class="mini-badge violet" style="margin-top: 18rpx;">{{ data.profile.level }}</view>
    </view>

    <view class="mini-space" />

    <view class="mini-grid-2">
      <view class="mini-card" style="padding: 28rpx;">
        <view class="mini-card-title">护理计划</view>
        <view v-for="item in data.carePlan" :key="item" class="mini-item" style="margin-top: 18rpx;">
          <view class="mini-item-title">建议</view>
          <view class="mini-item-copy">{{ item }}</view>
        </view>
      </view>
      <view class="mini-card" style="padding: 28rpx;">
        <view class="mini-card-title">档案摘要</view>
        <view class="mini-item" style="margin-top: 18rpx;">
          <view class="mini-item-title">过敏史</view>
          <view class="mini-item-copy">{{ data.healthArchive.allergies.join('、') }}</view>
        </view>
        <view class="mini-item" style="margin-top: 18rpx;">
          <view class="mini-item-title">生活习惯</view>
          <view class="mini-item-copy">{{ data.healthArchive.habits.join('、') }}</view>
        </view>
      </view>
    </view>

    <view class="mini-secondary" style="margin-top: 22rpx;" @click="openMiniPage('/pages/health/index')">查看完整健康档案</view>

    <MiniDock active="profile" />
  </view>
</template>
