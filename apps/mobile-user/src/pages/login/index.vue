<script setup lang="ts">
import { reactive, ref } from 'vue'

import { loginPortalUser } from '../../shared/portal'

const loading = ref(false)
const form = reactive({
  username: 'user01',
  password: '12345678',
})

async function handleLogin() {
  try {
    loading.value = true
    await loginPortalUser(form.username, form.password)
    uni.reLaunch({ url: '/pages/home/index' })
  } catch (error: any) {
    uni.showToast({ title: error.message || '登录失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <view class="page-wrap safe-top" style="display: flex; flex-direction: column; justify-content: center;">
    <view class="mini-card" style="padding: 40rpx;">
      <view class="mini-badge violet">AI 皮肤健康 · 智能随行</view>
      <view class="mini-title" style="margin-top: 28rpx;">上传图片、提交症状、查看 AI 结果与医生回复，一站式完成肤联智诊体验。</view>
      <view class="mini-subtitle">登录后可直接进入首页、图文问诊、AI 分析结果和知识问答页，适合答辩展示的小程序风格高保真界面。</view>

      <view class="mini-field" style="margin-top: 30rpx;">
        <view class="mini-field-label">账号</view>
        <input v-model="form.username" class="mini-input" placeholder="请输入账号" />
      </view>
      <view class="mini-field" style="margin-top: 22rpx;">
        <view class="mini-field-label">密码</view>
        <input v-model="form.password" password class="mini-input" placeholder="请输入密码" />
      </view>

      <view class="mini-primary" style="margin-top: 30rpx;" @click="handleLogin">
        {{ loading ? '正在进入…' : '进入我的健康空间' }}
      </view>
      <view class="mini-secondary" style="margin-top: 18rpx;" @click="form.username='user01'; form.password='12345678'">
        使用默认演示账号
      </view>
    </view>
  </view>
</template>
