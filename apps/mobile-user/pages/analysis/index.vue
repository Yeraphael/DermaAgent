<script setup lang="ts">
import { onLoad } from '@dcloudio/uni-app'
import { computed, ref } from 'vue'

import { deleteConsultation, fetchConsultationDetail, fetchMyConsultations } from '../../services/consultation'
import { formatDateTime, getRiskLabel, getStatusLabel, levelLabel, parseConsultationNarrative, sanitizeVisibleText, splitSegments } from '../../utils/display'
import { ensureLogin } from '../../utils/api'

const detail = ref<any>(null)
const loading = ref(false)
const errorMessage = ref('')
const caseId = ref(0)

const parsed = computed(() => parseConsultationNarrative(detail.value?.chief_complaint))
const possibleDirections = computed(() => splitSegments(detail.value?.ai_result?.possible_conditions).slice(0, 3))
const careSuggestions = computed(() => splitSegments(detail.value?.ai_result?.care_advice))
const imageObservation = computed(() => sanitizeVisibleText(detail.value?.ai_result?.image_observation, '已收到图片，系统正在整理图像观察要点。'))
const riskReminder = computed(() => sanitizeVisibleText(detail.value?.ai_result?.hospital_advice || detail.value?.ai_result?.high_risk_alert, '若症状持续加重、伴随渗液或发热，请及时线下就医。'))

async function loadDetail(id?: number) {
  if (!ensureLogin()) return

  try {
    loading.value = true
    errorMessage.value = ''

    let targetId = id || caseId.value
    if (!targetId) {
      const latest = await fetchMyConsultations(1, 1)
      targetId = latest.list[0]?.case_id || 0
    }

    if (!targetId) {
      detail.value = null
      return
    }

    caseId.value = targetId
    detail.value = await fetchConsultationDetail(targetId)
  } catch (error: any) {
    errorMessage.value = error.message || '分析结果加载失败'
  } finally {
    loading.value = false
  }
}

function previewImages(index: number) {
  const urls = (detail.value?.images || []).map((item: any) => item.file_url)
  uni.previewImage({
    current: urls[index],
    urls,
  })
}

function continueAsk() {
  if (!detail.value) return
  const prompt = `我想继续追问病例 ${detail.value.case_no}：${parsed.value.complaint || detail.value.summary_title}`
  uni.setStorageSync('qa_pending_ask', prompt)
  uni.switchTab({ url: '/pages/qa/index' })
}

function deleteCurrent() {
  if (!caseId.value) return
  uni.showModal({
    title: '确认删除该记录？',
    content: '删除后无法恢复。',
    success: async (res) => {
      if (!res.confirm) return
      try {
        await deleteConsultation(caseId.value)
        uni.showToast({ title: '删除成功', icon: 'success' })
        setTimeout(() => {
          uni.switchTab({ url: '/pages/history/index' })
        }, 250)
      } catch (error: any) {
        uni.showToast({ title: error.message || '删除失败，请稍后重试', icon: 'none' })
      }
    },
  })
}

onLoad((options) => {
  const id = Number(options?.caseId || 0)
  void loadDetail(id)
})
</script>

<template>
  <view class="page-wrap safe-top analysis-page">
    <view v-if="loading" class="surface-card analysis-card">
      <view class="section-title">正在加载分析结果</view>
      <view class="section-subtitle">请稍候，我们正在同步病例详情。</view>
    </view>

    <view v-else-if="errorMessage" class="surface-card analysis-card">
      <view class="section-title">分析结果加载失败</view>
      <view class="section-subtitle">{{ errorMessage }}</view>
      <view class="primary-btn" style="margin-top: 24rpx;" @click="loadDetail(caseId)">重新加载</view>
    </view>

    <view v-else-if="!detail" class="surface-card analysis-card">
      <view class="section-title">暂无分析记录</view>
      <view class="section-subtitle">完成一次图文问诊后，分析结果会展示在这里。</view>
      <view class="primary-btn" style="margin-top: 24rpx;" @click="uni.switchTab({ url: '/pages/consultation/index' })">去图文问诊</view>
    </view>

    <template v-else>
      <view class="surface-card analysis-card">
        <view class="section-title">智能分析</view>
        <view class="section-subtitle">基于上传信息与智能模型的综合分析，仅供参考，不能替代面诊诊断。</view>

        <view class="stat-grid" style="margin-top: 24rpx;">
          <view class="stat-card">
            <view class="label">病例编号</view>
            <view class="num">{{ detail.case_no }}</view>
          </view>
          <view class="stat-card">
            <view class="label">提交时间</view>
            <view class="num" style="font-size: 30rpx;">{{ formatDateTime(detail.submitted_at) }}</view>
          </view>
          <view class="stat-card">
            <view class="label">分析状态</view>
            <view class="num" style="font-size: 30rpx;">{{ getStatusLabel(detail.status) }}</view>
          </view>
          <view class="stat-card">
            <view class="label">风险等级</view>
            <view class="num" style="font-size: 30rpx;">{{ getRiskLabel(detail.risk_level) }}</view>
          </view>
        </view>
      </view>

      <view class="surface-card analysis-card">
        <view class="label">病例摘要</view>
        <view class="summary-item">
          <text>主诉描述：</text>
          <text>{{ parsed.complaint || sanitizeVisibleText(detail.summary_title) }}</text>
        </view>
        <view class="summary-item">
          <text>症状部位：</text>
          <text>{{ parsed.areas || '未填写' }}</text>
        </view>
        <view class="summary-item">
          <text>病程：</text>
          <text>{{ parsed.onsetDuration || detail.onset_duration || '未填写' }}</text>
        </view>
        <view class="summary-item">
          <text>伴随症状：</text>
          <text>瘙痒 {{ parsed.itchLevel || levelLabel(detail.itch_level || 0) }}，疼痛 {{ parsed.painLevel || levelLabel(detail.pain_level || 0) }}</text>
        </view>
        <view class="summary-item">
          <text>诱发因素：</text>
          <text>{{ parsed.medication || '暂未明确，可结合近期护肤、饮食和作息变化继续观察。' }}</text>
        </view>
      </view>

      <view class="surface-card analysis-card">
        <view class="label">图像观察</view>
        <scroll-view scroll-x class="analysis-images">
          <view
            v-for="(item, index) in detail.images"
            :key="item.image_id"
            class="analysis-images__item"
            @click="previewImages(index)"
          >
            <image :src="item.file_url" mode="aspectFill" class="analysis-images__img" />
          </view>
        </scroll-view>
        <view class="section-subtitle">{{ imageObservation }}</view>
      </view>

      <view class="surface-card analysis-card">
        <view class="label">可能相关方向</view>
        <view v-for="(item, index) in possibleDirections" :key="item" class="direction-card">
          <view class="direction-card__head">
            <view class="chip">{{ index === 0 ? '优先关注' : index === 1 ? '建议排查' : '补充参考' }}</view>
            <view class="label">{{ index === 2 ? '★★★☆☆' : '★★★★☆' }}</view>
          </view>
          <view class="direction-card__title">{{ sanitizeVisibleText(item) }}</view>
        </view>
      </view>

      <view class="surface-card analysis-card">
        <view class="label">护理建议</view>
        <view v-for="item in careSuggestions" :key="item" class="list-item">{{ sanitizeVisibleText(item) }}</view>
        <view v-if="!careSuggestions.length" class="list-item">温和清洁、加强保湿、避免刺激，并根据症状变化及时就诊。</view>
      </view>

      <view class="surface-card analysis-card">
        <view class="label">就医风险与提醒</view>
        <view class="risk-box">
          <view class="chip">{{ getRiskLabel(detail.risk_level) }}</view>
          <view class="section-subtitle">{{ riskReminder }}</view>
        </view>
      </view>

      <view class="surface-card analysis-card">
        <view class="label">医生回复</view>
        <view class="section-subtitle" v-if="detail.doctor_reply">
          {{ sanitizeVisibleText(detail.doctor_reply.doctor_name, '皮肤科医师') }}｜{{ formatDateTime(detail.doctor_reply.created_at) }}
        </view>
        <view class="reply-box">
          {{ sanitizeVisibleText(detail.doctor_reply?.content, '医生暂未回复，请耐心等待。收到回复后会在历史记录中同步更新。') }}
        </view>
      </view>

      <view class="bottom-submit">
        <view class="primary-btn" @click="continueAsk">继续追问</view>
        <view class="secondary-btn" style="margin-top: 12rpx;" @click="deleteCurrent">删除记录</view>
        <view class="bottom-submit__note">{{ sanitizeVisibleText(detail.ai_result?.disclaimer, '分析结果仅供参考，不能替代专业医疗建议。') }}</view>
      </view>
    </template>
  </view>
</template>

<style scoped lang="scss">
.analysis-page {
  padding-bottom: 220rpx;
}

.analysis-card {
  padding: 30rpx;
  margin-bottom: 18rpx;
}

.summary-item {
  margin-top: 16rpx;
  color: #17345f;
  font-size: 28rpx;
  line-height: 1.8;
}

.summary-item text:first-child {
  color: #7a8fb3;
}

.analysis-images {
  margin-top: 16rpx;
  white-space: nowrap;
}

.analysis-images__item {
  display: inline-block;
  width: 180rpx;
  height: 180rpx;
  margin-right: 16rpx;
}

.analysis-images__img {
  width: 100%;
  height: 100%;
  border-radius: 24rpx;
}

.direction-card,
.list-item,
.reply-box,
.risk-box {
  margin-top: 16rpx;
  padding: 22rpx;
  border: 1px solid rgba(166, 187, 224, 0.42);
  border-radius: 24rpx;
  background: rgba(248, 250, 255, 0.98);
}

.direction-card__head {
  display: flex;
  justify-content: space-between;
  gap: 12rpx;
}

.direction-card__title {
  margin-top: 12rpx;
  color: #15326a;
  font-size: 28rpx;
  font-weight: 700;
}

.list-item,
.reply-box {
  color: #17345f;
  font-size: 28rpx;
  line-height: 1.8;
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
