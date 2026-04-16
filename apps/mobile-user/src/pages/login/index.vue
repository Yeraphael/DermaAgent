<script setup lang="ts">
import { reactive, ref } from 'vue'

import { request, setSession } from '../../utils/api'

const loading = ref(false)
const form = reactive({
  username: 'user01',
  password: '12345678',
})

async function handleLogin() {
  try {
    loading.value = true
    const data = await request<any>('/auth/login', {
      method: 'POST',
      data: form,
    })
    setSession(data)
    uni.showToast({ title: '登录成功', icon: 'success' })
    setTimeout(() => {
      uni.switchTab({ url: '/pages/home/index' })
    }, 300)
  } catch (error: any) {
    uni.showToast({ title: error.message || '登录失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function usePreset() {
  form.username = 'user01'
  form.password = '12345678'
}
</script>

<template>
  <view class="page-wrap safe-top" style="display: flex; flex-direction: column; justify-content: center;">
    <view class="glass-card" style="padding: 40rpx;">
      <view class="chip" style="display: inline-flex;">肤联智诊 · 皮肤健康智慧助手</view>
      <view style="margin-top: 28rpx;" class="section-title">拍照上传 + 图文分析 + 医生协同，一站式完成皮肤问诊体验</view>
      <view class="section-subtitle">
        登录后可发起图文问诊、查看 AI 分析结果、进行皮肤知识问答，并持续维护个人健康档案。
      </view>

      <view style="margin-top: 32rpx;">
        <view class="label">账号</view>
        <input v-model="form.username" class="input-box" placeholder="请输入账号" />
      </view>
      <view style="margin-top: 22rpx;">
        <view class="label">密码</view>
        <input v-model="form.password" password class="input-box" placeholder="请输入密码" />
      </view>

      <view style="margin-top: 28rpx;" class="primary-btn" @click="handleLogin">
        {{ loading ? '登录中...' : '进入我的健康空间' }}
      </view>

      <view style="margin-top: 22rpx;" class="outline-btn" @click="usePreset">
        使用默认测试账号 user01 / 12345678
      </view>
    </view>
  </view>
</template>

