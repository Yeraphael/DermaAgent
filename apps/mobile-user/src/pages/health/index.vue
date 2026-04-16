<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app'
import { reactive } from 'vue'

import { ensureLogin, request } from '../../utils/api'

const form = reactive({
  allergy_history: '',
  past_medical_history: '',
  medication_history: '',
  skin_type: '',
  skin_sensitivity: '',
  sleep_pattern: '',
  diet_preference: '',
  special_notes: '',
})

async function loadData() {
  if (!ensureLogin()) return
  const data = await request<any>('/user/health-profile')
  Object.assign(form, data)
}

async function saveData() {
  try {
    await request('/user/health-profile', {
      method: 'PUT',
      data: form,
    })
    uni.showToast({ title: '健康档案已保存', icon: 'success' })
  } catch (error: any) {
    uni.showToast({ title: error.message || '保存失败', icon: 'none' })
  }
}

onShow(loadData)
</script>

<template>
  <view class="page-wrap safe-top">
    <view class="glass-card" style="padding: 34rpx;">
      <view class="section-title">健康档案</view>
      <view class="section-subtitle">完善既往史、肤质、敏感程度和生活习惯，便于后续 AI 与医生更准确理解你的皮肤状态。</view>

      <view style="display: grid; gap: 18rpx; margin-top: 24rpx;">
        <view>
          <view class="label">过敏史</view>
          <textarea v-model="form.allergy_history" class="textarea-box" />
        </view>
        <view>
          <view class="label">既往病史</view>
          <textarea v-model="form.past_medical_history" class="textarea-box" />
        </view>
        <view>
          <view class="label">近期用药</view>
          <textarea v-model="form.medication_history" class="textarea-box" />
        </view>
        <view>
          <view class="label">肤质</view>
          <input v-model="form.skin_type" class="input-box" placeholder="例如：敏感性 / 混合性" />
        </view>
        <view>
          <view class="label">敏感程度</view>
          <input v-model="form.skin_sensitivity" class="input-box" placeholder="例如：中度敏感" />
        </view>
        <view>
          <view class="label">睡眠情况</view>
          <input v-model="form.sleep_pattern" class="input-box" placeholder="例如：偶尔熬夜" />
        </view>
        <view>
          <view class="label">饮食偏好</view>
          <input v-model="form.diet_preference" class="input-box" placeholder="例如：偏甜偏辣" />
        </view>
        <view>
          <view class="label">补充备注</view>
          <textarea v-model="form.special_notes" class="textarea-box" />
        </view>
      </view>

      <view style="margin-top: 30rpx;" class="primary-btn" @click="saveData">保存健康档案</view>
    </view>
  </view>
</template>
