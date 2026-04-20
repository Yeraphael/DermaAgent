<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app'
import { reactive, ref } from 'vue'

import { askPortalQuestion, getPortalQaSnapshot } from '../../shared/portal'
import { ensurePortalLogin } from '../../utils/miniPortal'

const form = reactive({
  question: '湿疹和过敏有什么区别？',
})
const answer = ref<Awaited<ReturnType<typeof askPortalQuestion>> | null>(null)
const snapshot = ref(getPortalQaSnapshot())

async function askQuestion() {
  if (!form.question.trim()) {
    uni.showToast({ title: '请输入问题', icon: 'none' })
    return
  }
  answer.value = await askPortalQuestion(form.question)
  snapshot.value = getPortalQaSnapshot()
}

onShow(() => {
  if (!ensurePortalLogin()) return
  snapshot.value = getPortalQaSnapshot()
})
</script>

<template>
  <view class="page-wrap safe-top">
    <view class="mini-card" style="padding: 32rpx;">
      <view class="mini-eyebrow">知识问答</view>
      <view class="mini-title" style="margin-top: 12rpx;">关于你的皮肤问题，再多问一步</view>
      <view class="mini-subtitle">围绕护理、泛红、敏感、痘痘和是否建议就医等问题给出可理解的 AI 回答。</view>

      <view class="mini-field" style="margin-top: 24rpx;">
        <view class="mini-field-label">输入你的问题</view>
        <textarea v-model="form.question" class="mini-textarea" maxlength="180" placeholder="例如：面部泛红时还能刷酸吗？" />
      </view>
      <view class="mini-chips" style="margin-top: 18rpx;">
        <view v-for="item in snapshot.suggestions" :key="item" class="mini-chip" @click="form.question = item">{{ item }}</view>
      </view>
      <view class="mini-primary" style="margin-top: 26rpx;" @click="askQuestion">获取 AI 回答</view>
    </view>

    <view v-if="answer" class="mini-space" />

    <view v-if="answer" class="mini-card" style="padding: 30rpx;">
      <view class="mini-card-title">AI 回答</view>
      <view class="mini-subtitle">{{ answer.answer }}</view>
      <view class="mini-item-meta" style="margin-top: 16rpx;">参考来源：{{ answer.reference }}</view>
    </view>

    <view class="mini-space" />

    <view class="mini-card" style="padding: 30rpx;">
      <view class="mini-card-title">最近问答</view>
      <view v-for="item in snapshot.history" :key="item.id" class="mini-item" style="margin-top: 18rpx;">
        <view class="mini-item-title">{{ item.question }}</view>
        <view class="mini-item-copy">{{ item.answer }}</view>
        <view class="mini-item-meta">{{ item.createdAt }} · {{ item.reference }}</view>
      </view>
    </view>

    <MiniDock active="qa" />
  </view>
</template>
