<script setup lang="ts">
import { reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

import { ensureLogin, request, uploadImage } from '../../utils/api'

const loading = ref(false)
const form = reactive({
  chief_complaint: '',
  onset_duration: '3天',
  itch_level: 2,
  pain_level: 1,
  spread_flag: 0,
  need_doctor_review: 1,
})
const imageFiles = ref<Array<{ path: string; url?: string }>>([])
const onsetOptions = ['3天', '1周', '2周', '1个月', '反复半年', '近三天明显加重']

onShow(() => {
  ensureLogin()
})

function chooseImages() {
  uni.chooseImage({
    count: 3,
    success: (res) => {
      imageFiles.value = res.tempFilePaths.map((path) => ({ path }))
    },
  })
}

async function submitConsultation() {
  try {
    if (!form.chief_complaint.trim()) {
      uni.showToast({ title: '请先填写症状描述', icon: 'none' })
      return
    }
    loading.value = true
    const urls: string[] = []
    for (const file of imageFiles.value) {
      const uploaded = await uploadImage(file.path)
      urls.push(uploaded.file_url)
      file.url = uploaded.file_url
    }
    const data = await request<any>('/consultations', {
      method: 'POST',
      data: {
        ...form,
        image_urls: urls,
      },
    })
    uni.showToast({ title: '问诊已提交', icon: 'success' })
    setTimeout(() => {
      uni.navigateTo({ url: `/pages/analysis/index?caseId=${data.consultation.case_id}` })
    }, 400)
  } catch (error: any) {
    uni.showToast({ title: error.message || '提交失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <view class="page-wrap safe-top">
    <view class="glass-card" style="padding: 34rpx;">
      <view class="section-title">图文问诊</view>
      <view class="section-subtitle">上传清晰皮肤图片并描述症状，系统会先给出 AI 辅助分析，再进入医生协同环节。</view>

      <view style="margin-top: 24rpx;">
        <view class="label">症状描述</view>
        <textarea v-model="form.chief_complaint" class="textarea-box" maxlength="300" placeholder="例如：脸颊发红发痒，换了护肤品后明显加重，最近三天更明显。" />
      </view>

      <view style="margin-top: 22rpx;">
        <view class="label">起病时长</view>
        <picker :range="onsetOptions" @change="form.onset_duration = onsetOptions[$event.detail.value]">
          <view class="picker-box">{{ form.onset_duration }}</view>
        </picker>
      </view>

      <view class="stat-grid" style="margin-top: 22rpx;">
        <view class="glass-card" style="padding: 24rpx;">
          <view class="label">瘙痒程度</view>
          <slider :value="form.itch_level" min="0" max="5" show-value @change="form.itch_level = $event.detail.value" activeColor="#59e4c2" />
        </view>
        <view class="glass-card" style="padding: 24rpx;">
          <view class="label">疼痛程度</view>
          <slider :value="form.pain_level" min="0" max="5" show-value @change="form.pain_level = $event.detail.value" activeColor="#82b9ff" />
        </view>
      </view>

      <view style="display: flex; gap: 16rpx; margin-top: 20rpx;">
        <view class="chip" @click="form.spread_flag = form.spread_flag === 1 ? 0 : 1">{{ form.spread_flag === 1 ? '存在扩散' : '未扩散' }}</view>
        <view class="chip" @click="form.need_doctor_review = form.need_doctor_review === 1 ? 0 : 1">{{ form.need_doctor_review === 1 ? '医生复核已开启' : '仅查看 AI 结果' }}</view>
      </view>

      <view style="margin-top: 24rpx;">
        <view class="label">皮肤图片</view>
        <view class="outline-btn" style="margin-top: 12rpx;" @click="chooseImages">选择图片（最多 3 张）</view>
        <view style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16rpx; margin-top: 18rpx;">
          <image v-for="item in imageFiles" :key="item.path" :src="item.path" mode="aspectFill" style="width: 100%; height: 180rpx; border-radius: 24rpx;" />
        </view>
      </view>

      <view style="margin-top: 30rpx;" class="primary-btn" @click="submitConsultation">
        {{ loading ? '正在上传并分析...' : '提交问诊并生成分析结果' }}
      </view>
    </view>
  </view>
</template>

