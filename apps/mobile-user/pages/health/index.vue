<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app'
import { ref } from 'vue'

import { deleteConsultation } from '../../services/consultation'
import { fetchHealthArchive } from '../../services/user'
import { formatDate, getRiskLabel, guessSuggestionDetail, sanitizeVisibleText } from '../../utils/display'
import { ensureLogin } from '../../utils/api'

const archive = ref<any>(null)
const loading = ref(false)
const expandedIndex = ref(0)

async function loadData() {
  if (!ensureLogin()) return

  try {
    loading.value = true
    archive.value = await fetchHealthArchive()
  } finally {
    loading.value = false
  }
}

function removeCase(caseId: number) {
  uni.showModal({
    title: '确认删除该记录？',
    content: '删除后无法恢复。',
    success: async (res) => {
      if (!res.confirm) return

      const backup = [...(archive.value?.recent_cases || [])]
      archive.value.recent_cases = archive.value.recent_cases.filter((item: any) => item.case_id !== caseId)

      try {
        await deleteConsultation(caseId)
        uni.showToast({ title: '删除成功', icon: 'success' })
      } catch (error: any) {
        archive.value.recent_cases = backup
        uni.showToast({ title: error.message || '删除失败，请稍后重试', icon: 'none' })
      }
    },
  })
}

onShow(() => {
  void loadData()
})
</script>

<template>
  <view class="page-wrap safe-top health-page">
    <view class="surface-card health-card">
      <view class="section-title">健康档案</view>
      <view class="section-subtitle">记录您的皮肤健康信息与问诊历史，跟踪风险趋势，沉淀护理建议。</view>
    </view>

    <view v-if="loading" class="surface-card health-card">
      <view class="section-subtitle" style="margin-top: 0;">正在加载健康档案...</view>
    </view>

    <template v-else-if="archive">
      <view class="stat-grid">
        <view class="stat-card">
          <view class="label">皮肤类型</view>
          <view class="num">{{ sanitizeVisibleText(archive.stats.skin_type, '未完善') }}</view>
          <view class="section-subtitle">更新于 {{ archive.stats.skin_type_updated_at || '--' }}</view>
        </view>
        <view class="stat-card">
          <view class="label">最近 30 天问诊</view>
          <view class="num">{{ archive.stats.consultations_30d }} 次</view>
          <view class="section-subtitle">较上期 {{ archive.stats.consultations_30d_delta || 0 }}%</view>
        </view>
        <view class="stat-card">
          <view class="label">医生回复</view>
          <view class="num">{{ archive.stats.doctor_replies_30d }} 次</view>
          <view class="section-subtitle">累计 {{ archive.stats.doctor_replies_total }} 次</view>
        </view>
        <view class="stat-card">
          <view class="label">护理计划</view>
          <view class="num">{{ sanitizeVisibleText(archive.stats.care_plan_status, '待建立') }}</view>
          <view class="section-subtitle">更新于 {{ archive.stats.care_plan_updated_at || '--' }}</view>
        </view>
      </view>

      <view class="surface-card health-card">
        <view class="health-card__head">
          <view>
            <view class="label">基础信息</view>
            <view class="section-subtitle">姓名：{{ sanitizeVisibleText(archive.basic_info.real_name, '未填写') }}</view>
            <view class="section-subtitle">性别：{{ sanitizeVisibleText(archive.basic_info.gender, '未填写') }}</view>
            <view class="section-subtitle">年龄：{{ archive.basic_info.age || '--' }}</view>
            <view class="section-subtitle">手机号：{{ archive.basic_info.phone || '--' }}</view>
          </view>
          <view class="text-btn" @click="uni.navigateTo({ url: '/pages/profile/index' })">编辑资料</view>
        </view>
      </view>

      <view class="surface-card health-card">
        <view class="label">风险趋势</view>
        <view v-for="item in archive.risk_trend" :key="item.level" class="trend-item">
          <view class="trend-item__head">
            <text>{{ item.label }}</text>
            <text>{{ item.percentage }}%</text>
          </view>
          <view class="trend-item__track">
            <view class="trend-item__bar" :style="{ width: `${item.percentage}%`, background: item.level === 'HIGH' ? '#ef5b6d' : item.level === 'MEDIUM' ? '#f29c38' : '#18b88d' }" />
          </view>
          <view class="section-subtitle">{{ item.days }} 天</view>
        </view>
      </view>

      <view class="surface-card health-card">
        <view class="label">最近病例</view>
        <view v-for="item in archive.recent_cases" :key="item.case_id" class="case-item">
          <view class="case-item__main">
            <view class="case-item__title">{{ sanitizeVisibleText(item.title, '皮肤健康记录') }}</view>
            <view class="section-subtitle">{{ formatDate(item.submitted_at) }}</view>
            <view class="chip-row" style="margin-top: 12rpx;">
              <view class="status-chip amber">{{ getRiskLabel(item.risk_level) }}</view>
            </view>
          </view>
          <view class="case-item__actions">
            <view class="secondary-btn" @click="uni.navigateTo({ url: `/pages/analysis/index?caseId=${item.case_id}` })">查看详情</view>
            <view class="secondary-btn" @click="removeCase(item.case_id)">删除</view>
          </view>
        </view>
      </view>

      <view class="surface-card health-card">
        <view class="label">护理建议沉淀</view>
        <view v-for="(item, index) in archive.care_suggestions" :key="item" class="suggestion-item">
          <view class="suggestion-item__head" @click="expandedIndex = expandedIndex === index ? -1 : index">
            <text>{{ sanitizeVisibleText(item) }}</text>
            <text>{{ expandedIndex === index ? '收起' : '展开' }}</text>
          </view>
          <view v-if="expandedIndex === index" class="section-subtitle">{{ guessSuggestionDetail(item) }}</view>
        </view>
      </view>
    </template>
  </view>
</template>

<style scoped lang="scss">
.health-page {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.health-card {
  padding: 28rpx;
}

.health-card__head {
  display: flex;
  justify-content: space-between;
  gap: 16rpx;
}

.trend-item {
  margin-top: 18rpx;
}

.trend-item__head {
  display: flex;
  justify-content: space-between;
  gap: 12rpx;
  color: #17345f;
  font-size: 26rpx;
}

.trend-item__track {
  height: 16rpx;
  border-radius: 999rpx;
  margin-top: 12rpx;
  background: rgba(226, 233, 247, 0.92);
  overflow: hidden;
}

.trend-item__bar {
  height: 100%;
  border-radius: inherit;
}

.case-item,
.suggestion-item {
  margin-top: 18rpx;
  padding: 22rpx;
  border: 1px solid rgba(166, 187, 224, 0.42);
  border-radius: 24rpx;
  background: rgba(248, 250, 255, 0.98);
}

.case-item__title {
  color: #15326a;
  font-size: 28rpx;
  font-weight: 700;
}

.case-item__actions {
  display: flex;
  gap: 12rpx;
  margin-top: 16rpx;
}

.case-item__actions .secondary-btn {
  flex: 1;
}

.suggestion-item__head {
  display: flex;
  justify-content: space-between;
  gap: 14rpx;
  color: #15326a;
  font-size: 28rpx;
  font-weight: 700;
}
</style>
