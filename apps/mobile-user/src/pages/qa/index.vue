<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app'
import { reactive, ref } from 'vue'

import { ensureLogin, request } from '../../utils/api'

const form = reactive({
  question: '痘痘反复长是不是和熬夜有关？',
})
const answer = ref<any>(null)
const historyList = ref<any[]>([])
const hotSamples = ['痘痘反复长是不是和熬夜有关？', '脸上过敏泛红时可以继续刷酸吗？', '湿疹反复瘙痒应该怎样护理？']

async function fetchHistory() {
  historyList.value = (await request<any>('/rag/qa/history?page=1&page_size=8')).list
}

async function askQuestion() {
  if (!form.question.trim()) {
    uni.showToast({ title: '请先输入问题', icon: 'none' })
    return
  }
  try {
    answer.value = await request('/rag/qa', {
      method: 'POST',
      data: { question: form.question },
    })
    await fetchHistory()
  } catch (error: any) {
    uni.showToast({ title: error.message || '提问失败', icon: 'none' })
  }
}

onShow(async () => {
  if (!ensureLogin()) return
  await fetchHistory()
})
</script>

<template>
  <view class="page-wrap safe-top">
    <view class="glass-card" style="padding: 32rpx;">
      <view class="section-title">皮肤健康知识问答</view>
      <view class="section-subtitle">后端通过 mock RAG 检索知识片段增强回答，适合做护理建议和风险提醒参考。</view>

      <view style="margin-top: 24rpx;">
        <textarea v-model="form.question" class="textarea-box" maxlength="180" placeholder="输入你关心的皮肤护理或就医相关问题" />
      </view>
      <view class="chip-row" style="margin-top: 18rpx;">
        <view v-for="sample in hotSamples" :key="sample" class="chip" @click="form.question = sample">{{ sample }}</view>
      </view>
      <view style="margin-top: 24rpx;" class="primary-btn" @click="askQuestion">获取回答</view>
    </view>

    <view v-if="answer" style="height: 20rpx;" />

    <view v-if="answer" class="glass-card" style="padding: 30rpx;">
      <view class="section-title" style="font-size: 34rpx;">AI 回答</view>
      <view style="margin-top: 18rpx; font-size: 28rpx; line-height: 1.9;">{{ answer.answer }}</view>
      <view style="margin-top: 18rpx; color: #ffb0b0;">{{ answer.risk_hint }}</view>
      <view style="margin-top: 18rpx;" class="label">检索参考</view>
      <view v-for="item in answer.references" :key="item.chunk_id" style="margin-top: 14rpx; padding: 22rpx; border-radius: 24rpx; background: rgba(9, 19, 31, 0.72);">
        <view style="font-size: 28rpx; font-weight: 600;">{{ item.document_title }}</view>
        <view class="section-subtitle">{{ item.snippet }}</view>
      </view>
    </view>

    <view style="height: 20rpx;" />

    <view class="glass-card" style="padding: 30rpx;">
      <view class="section-title" style="font-size: 34rpx;">最近问答</view>
      <view v-for="item in historyList" :key="item.qa_id" style="margin-top: 18rpx; padding: 24rpx; border-radius: 28rpx; background: rgba(9, 19, 31, 0.7);">
        <view style="font-size: 28rpx; font-weight: 600;">{{ item.question }}</view>
        <view class="section-subtitle">{{ item.answer }}</view>
      </view>
    </view>
  </view>
</template>

