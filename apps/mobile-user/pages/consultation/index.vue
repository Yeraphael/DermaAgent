<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app'
import { computed, reactive, ref } from 'vue'

import { createConsultation } from '../../services/consultation'
import { buildConsultationNarrative, levelLabel, SYMPTOM_LEVELS } from '../../utils/display'
import { ensureLogin, uploadImage } from '../../utils/api'

const submitting = ref(false)
const images = ref<Array<{ path: string; size?: number }>>([])
const onsetOptions = ['1 天内', '2 天内', '1 周内', '1 个月内', '超过 1 个月']
const spreadOptions = ['否', '是', '不确定']
const medicationOptions = ['否', '是', '不确定']
const bodyParts = ['面部', '头皮', '颈部', '躯干', '四肢', '私密部位', '其他']

const form = reactive({
  description: '',
  onsetDuration: '1 周内',
  spread: '否',
  itchLevel: 1,
  painLevel: 1,
  areas: ['面部'],
  medication: '否',
})

const countText = computed(() => `${form.description.trim().length}/300`)

onShow(() => {
  ensureLogin()
})

function toast(title: string) {
  uni.showToast({ title, icon: 'none' })
}

function toggleArea(area: string) {
  if (form.areas.includes(area)) {
    form.areas = form.areas.filter((item) => item !== area)
    return
  }
  form.areas = [...form.areas, area]
}

function removeImage(index: number) {
  images.value.splice(index, 1)
}

function chooseImages() {
  uni.chooseImage({
    count: Math.max(1, 5 - images.value.length),
    success: (res) => {
      const next = res.tempFiles
        .filter((file) => {
          const path = file.path.toLowerCase()
          if (!/\.(jpg|jpeg|png|webp)$/.test(path)) {
            toast('仅支持 JPG、PNG、WebP 图片')
            return false
          }
          if ((file.size || 0) > 10 * 1024 * 1024) {
            toast('单张图片不能超过 10MB')
            return false
          }
          return true
        })
        .map((file) => ({ path: file.path, size: file.size }))

      images.value = [...images.value, ...next].slice(0, 5)
    },
  })
}

async function submit() {
  if (!images.value.length) {
    toast('请至少上传 1 张皮肤图片')
    return
  }
  if (!form.description.trim()) {
    toast('请详细描述您的症状')
    return
  }

  try {
    submitting.value = true
    const uploaded = []
    for (const item of images.value) {
      uploaded.push(await uploadImage(item.path))
    }

    const narrative = buildConsultationNarrative({
      description: form.description,
      onsetDuration: form.onsetDuration,
      spread: form.spread,
      itchLevel: levelLabel(form.itchLevel),
      painLevel: levelLabel(form.painLevel),
      areas: form.areas,
      medication: form.medication,
    })

    const result = await createConsultation({
      chief_complaint: narrative,
      onset_duration: form.onsetDuration,
      itch_level: form.itchLevel,
      pain_level: form.painLevel,
      spread_flag: form.spread === '是' ? 1 : 0,
      need_doctor_review: form.spread === '是' || form.itchLevel >= 3 || form.painLevel >= 3 ? 1 : 0,
      image_urls: uploaded.map((item) => item.file_url),
    })

    uni.showToast({ title: '问诊提交成功', icon: 'success' })
    setTimeout(() => {
      uni.navigateTo({ url: `/pages/analysis/index?caseId=${result.consultation.case_id}` })
    }, 250)
  } catch (error: any) {
    toast(error.message || '提交失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <view class="page-wrap safe-top consultation-page">
    <view class="surface-card consultation-card">
      <view class="section-title">图文问诊</view>
      <view class="section-subtitle">上传皮肤图片并描述症状，医生将为您提供专业建议。</view>

      <view class="form-block">
        <view class="label">1. 上传皮肤图片（最多 5 张）</view>
        <view class="secondary-btn" @click="chooseImages">点击选择图片</view>
        <view class="section-subtitle" style="margin-top: 10rpx;">支持 JPG、PNG、WebP，单张不超过 10MB</view>

        <view class="image-grid">
          <view v-for="(item, index) in images" :key="item.path" class="image-grid__item">
            <image :src="item.path" mode="aspectFill" class="image-grid__img" />
            <view class="image-grid__remove" @click.stop="removeImage(index)">×</view>
          </view>
        </view>
      </view>

      <view class="form-block">
        <view class="label">2. 症状描述</view>
        <textarea
          v-model="form.description"
          class="textarea-box"
          maxlength="300"
          placeholder="请详细描述您的症状，如出现时间、部位、颜色、形态、伴随感受等..."
        />
        <view class="count-text">{{ countText }}</view>
      </view>

      <view class="form-block">
        <view class="label">3. 发病时长</view>
        <picker :range="onsetOptions" @change="form.onsetDuration = onsetOptions[$event.detail.value]">
          <view class="picker-box">{{ form.onsetDuration }}</view>
        </picker>
      </view>

      <view class="form-block">
        <view class="label">4. 是否扩散</view>
        <view class="choice-row">
          <view
            v-for="item in spreadOptions"
            :key="item"
            class="choice-chip"
            :class="{ active: form.spread === item }"
            @click="form.spread = item"
          >
            {{ item }}
          </view>
        </view>
      </view>

      <view class="form-block">
        <view class="label">5. 瘙痒程度</view>
        <slider :value="form.itchLevel" min="0" max="4" activeColor="#2f7dff" block-color="#2f7dff" @change="form.itchLevel = $event.detail.value" />
        <view class="slider-labels">
          <view v-for="item in SYMPTOM_LEVELS" :key="item">{{ item }}</view>
        </view>
        <view class="section-subtitle" style="margin-top: 10rpx;">当前：{{ levelLabel(form.itchLevel) }}</view>
      </view>

      <view class="form-block">
        <view class="label">6. 疼痛程度</view>
        <slider :value="form.painLevel" min="0" max="4" activeColor="#18c8be" block-color="#18c8be" @change="form.painLevel = $event.detail.value" />
        <view class="slider-labels">
          <view v-for="item in SYMPTOM_LEVELS" :key="item">{{ item }}</view>
        </view>
        <view class="section-subtitle" style="margin-top: 10rpx;">当前：{{ levelLabel(form.painLevel) }}</view>
      </view>

      <view class="form-block">
        <view class="label">7. 发生部位</view>
        <view class="choice-row">
          <view
            v-for="item in bodyParts"
            :key="item"
            class="choice-chip"
            :class="{ active: form.areas.includes(item) }"
            @click="toggleArea(item)"
          >
            {{ item }}
          </view>
        </view>
      </view>

      <view class="form-block">
        <view class="label">8. 是否使用过药物或护肤品</view>
        <view class="choice-row">
          <view
            v-for="item in medicationOptions"
            :key="item"
            class="choice-chip"
            :class="{ active: form.medication === item }"
            @click="form.medication = item"
          >
            {{ item }}
          </view>
        </view>
      </view>

      <view class="surface-card side-card">
        <view class="label">提交说明</view>
        <view class="section-subtitle">提交后，系统会先生成智能分析结果，医生会在 24 小时内查看并给出专业回复。</view>
      </view>

      <view class="surface-card side-card">
        <view class="label">拍摄建议</view>
        <view class="section-subtitle">保证光线充足、对焦清晰，尽量同时拍摄全景和局部特写。</view>
      </view>
    </view>

    <view class="bottom-submit">
      <view class="primary-btn" @click="submit">
        {{ submitting ? '提交中...' : '提交问诊' }}
      </view>
      <view class="bottom-submit__note">所有信息将严格保密，仅用于医生诊断与建议。</view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.consultation-page {
  padding-bottom: 220rpx;
}

.consultation-card {
  padding: 30rpx;
}

.form-block {
  margin-top: 24rpx;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16rpx;
  margin-top: 18rpx;
}

.image-grid__item {
  position: relative;
  height: 180rpx;
}

.image-grid__img {
  width: 100%;
  height: 100%;
  border-radius: 24rpx;
}

.image-grid__remove {
  position: absolute;
  top: 10rpx;
  right: 10rpx;
  width: 40rpx;
  height: 40rpx;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  background: rgba(239, 91, 109, 0.9);
}

.count-text {
  margin-top: 10rpx;
  color: #7a8fb3;
  font-size: 22rpx;
  text-align: right;
}

.choice-row {
  display: flex;
  flex-wrap: wrap;
  gap: 14rpx;
  margin-top: 12rpx;
}

.choice-chip {
  padding: 16rpx 22rpx;
  border: 1px solid rgba(166, 187, 224, 0.42);
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.96);
  color: #5a7298;
  font-size: 24rpx;
}

.choice-chip.active {
  border-color: rgba(47, 125, 255, 0.46);
  background: rgba(47, 125, 255, 0.1);
  color: #2f7dff;
}

.slider-labels {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8rpx;
  margin-top: 8rpx;
  color: #7a8fb3;
  font-size: 22rpx;
  text-align: center;
}

.side-card {
  margin-top: 20rpx;
  padding: 24rpx;
}

.bottom-submit {
  position: fixed;
  left: 24rpx;
  right: 24rpx;
  bottom: 24rpx;
  z-index: 20;
  padding: 20rpx;
  border: 1px solid rgba(166, 187, 224, 0.42);
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 22rpx 70rpx rgba(115, 143, 198, 0.16);
}

.bottom-submit__note {
  margin-top: 12rpx;
  color: #7a8fb3;
  font-size: 22rpx;
  text-align: center;
}
</style>
