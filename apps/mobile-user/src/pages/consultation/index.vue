<script setup lang="ts">
import { reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

import { buildVisualStyle, submitPortalConsultation } from '../../shared/portal'
import { ensurePortalLogin, openMiniPage } from '../../utils/miniPortal'

const loading = ref(false)
const previews = ref<string[]>([])
const form = reactive({
  description: '',
  onsetDuration: '2 天内',
  itchLevel: 3,
  painLevel: 1,
  spreadFlag: false,
  spreadParts: ['面部'] as string[],
})

function chooseImages() {
  uni.chooseImage({
    count: 5,
    success: (res) => {
      previews.value = res.tempFilePaths
    },
  })
}

function toggleSpreadPart(part: string) {
  if (form.spreadParts.includes(part)) {
    form.spreadParts = form.spreadParts.filter((item) => item !== part)
  } else {
    form.spreadParts = [...form.spreadParts, part]
  }
}

async function submitConsultation() {
  if (!form.description.trim()) {
    uni.showToast({ title: '请先填写症状描述', icon: 'none' })
    return
  }
  loading.value = true
  const result = await submitPortalConsultation({
    description: form.description,
    onsetDuration: form.onsetDuration,
    itchLevel: form.itchLevel,
    painLevel: form.painLevel,
    spreadFlag: form.spreadFlag,
    spreadParts: form.spreadParts,
    visuals: previews.value,
  })
  loading.value = false
  uni.showToast({ title: '问诊已提交', icon: 'success' })
  setTimeout(() => {
    openMiniPage(`/pages/analysis/index?caseId=${result.caseId}`)
  }, 280)
}

onShow(() => {
  ensurePortalLogin()
})
</script>

<template>
  <view class="page-wrap safe-top">
    <view class="mini-card" style="padding: 34rpx;">
      <view class="mini-eyebrow">图文问诊</view>
      <view class="mini-title" style="margin-top: 12rpx;">提交你的皮肤问题</view>
      <view class="mini-subtitle">上传 1-5 张皮肤图片，补充症状描述、发病时长、瘙痒和疼痛程度，系统会自动生成 AI 分析结果。</view>

      <view class="mini-field" style="margin-top: 24rpx;">
        <view class="mini-field-label">上传皮肤图片（1-5 张）</view>
        <view class="mini-secondary" @click="chooseImages">选择图片</view>
        <view class="mini-visuals" style="margin-top: 16rpx;">
          <view v-for="item in previews.slice(0, 5)" :key="item" class="mini-visual" :style="buildVisualStyle(item)" />
          <view v-for="index in Math.max(0, 5 - previews.length)" :key="index" class="mini-visual mini-plus">+</view>
        </view>
      </view>

      <view class="mini-field" style="margin-top: 24rpx;">
        <view class="mini-field-label">症状描述</view>
        <textarea v-model="form.description" class="mini-textarea" maxlength="300" placeholder="例如：面颊泛红伴瘙痒，最近更换护肤品后加重。" />
      </view>

      <view class="mini-grid-2" style="margin-top: 22rpx;">
        <view class="mini-field">
          <view class="mini-field-label">发病时长</view>
          <picker :range="['今天', '2 天内', '3 天内', '1 周内', '1 个月']" @change="form.onsetDuration = ['今天', '2 天内', '3 天内', '1 周内', '1 个月'][$event.detail.value]">
            <view class="mini-picker">{{ form.onsetDuration }}</view>
          </picker>
        </view>
        <view class="mini-field">
          <view class="mini-field-label">是否扩散</view>
          <view class="mini-segment">
            <view class="mini-segment-item" :class="{ active: !form.spreadFlag }" @click="form.spreadFlag = false">否</view>
            <view class="mini-segment-item" :class="{ active: form.spreadFlag }" @click="form.spreadFlag = true">是</view>
          </view>
        </view>
      </view>

      <view class="mini-grid-2" style="margin-top: 22rpx;">
        <view class="mini-field">
          <view class="mini-field-label">瘙痒程度 {{ form.itchLevel }}</view>
          <slider :value="form.itchLevel" min="0" max="5" show-value activeColor="#3A8BFF" @change="form.itchLevel = $event.detail.value" />
        </view>
        <view class="mini-field">
          <view class="mini-field-label">疼痛程度 {{ form.painLevel }}</view>
          <slider :value="form.painLevel" min="0" max="5" show-value activeColor="#8A5CFF" @change="form.painLevel = $event.detail.value" />
        </view>
      </view>

      <view class="mini-field" style="margin-top: 22rpx;">
        <view class="mini-field-label">扩散部位（可多选）</view>
        <view class="mini-chips">
          <view
            v-for="item in ['面部', '颈部', '手臂', '躯干', '其他']"
            :key="item"
            class="mini-chip"
            :class="{ active: form.spreadParts.includes(item) }"
            @click="toggleSpreadPart(item)"
          >
            {{ item }}
          </view>
        </view>
      </view>

      <view class="mini-primary" style="margin-top: 28rpx;" @click="submitConsultation">
        {{ loading ? '正在生成 AI 结果…' : '提交问诊' }}
      </view>
    </view>

    <MiniDock active="consultation" />
  </view>
</template>
