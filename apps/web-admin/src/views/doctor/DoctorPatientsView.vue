<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'

import EmptyState from '@/components/EmptyState.vue'
import PanelCard from '@/components/PanelCard.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import TrendChart from '@/components/TrendChart.vue'
import {
  fetchDoctorPatientDetail,
  fetchDoctorPatients,
  type DoctorPatientDetail,
  type DoctorPatientListItem,
} from '@/api/workspace'
import {
  cleanVisibleText,
  formatDateTime,
  healthScoreTone,
  riskLabel,
  riskTone,
  resolveAvatar,
  splitVisibleText,
  statusLabel,
  statusTone,
} from '@/utils/workspace'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const detailLoading = ref(false)
const keyword = ref('')
const patients = ref<DoctorPatientListItem[]>([])
const detail = ref<DoctorPatientDetail | null>(null)

const filteredPatients = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  return patients.value.filter((item) => {
    if (!query) return true
    const text = [
      item.profile.real_name,
      item.account.username,
      item.account.phone,
      item.profile.city,
      ...item.tags,
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()
    return text.includes(query)
  })
})

const historyCases = computed(() => detail.value?.history_cases || [])
const careSuggestions = computed(() => detail.value?.care_suggestions || [])
const allergyItems = computed(() => splitVisibleText(detail.value?.health_profile?.allergy_history))
const medicationItems = computed(() => splitVisibleText(detail.value?.health_profile?.medication_history))
const historyItems = computed(() => splitVisibleText(detail.value?.health_profile?.past_medical_history))

async function loadPatients() {
  try {
    loading.value = true
    const result = await fetchDoctorPatients(keyword.value)
    patients.value = result
    const routeId = Number(route.params.userId)
    const matched = routeId ? result.find((item) => item.account.account_id === routeId) : null
    const targetId = matched?.account.account_id || result[0]?.account.account_id
    if (targetId && routeId !== targetId) {
      router.replace(`/doctor/patients/${targetId}`)
    } else if (!targetId) {
      detail.value = null
    }
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    loading.value = false
  }
}

async function loadDetail(userId: number) {
  try {
    detailLoading.value = true
    detail.value = await fetchDoctorPatientDetail(userId)
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    detailLoading.value = false
  }
}

function selectPatient(userId: number) {
  router.replace(`/doctor/patients/${userId}`)
}

function openCase(caseId: number) {
  router.push(`/doctor/consultations/${caseId}`)
}

watch(
  () => route.params.userId,
  async (value) => {
    const userId = Number(value)
    if (userId) {
      await loadDetail(userId)
    }
  },
)

onMounted(loadPatients)
</script>

<template>
  <section class="split-grid split-grid--patient">
    <PanelCard title="患者搜索" subtitle="统一查看基础资料、健康标签与长期病例轨迹。">
      <div class="form-field">
        <label>搜索患者姓名、手机号或标签</label>
        <input
          v-model="keyword"
          class="ghost-input"
          placeholder="例如：李婉晴 / 敏感肌 / 北京"
          @keydown.enter.prevent="loadPatients"
        />
      </div>

      <div class="action-row" style="margin-top: 14px;">
        <button type="button" class="primary-button" @click="loadPatients">刷新患者列表</button>
      </div>

      <div v-if="filteredPatients.length" class="list-panel" style="margin-top: 18px;" v-loading="loading">
        <article
          v-for="item in filteredPatients"
          :key="item.account.account_id"
          class="list-row"
          :class="{ 'is-active': detail?.account.account_id === item.account.account_id }"
          @click="selectPatient(item.account.account_id)"
        >
          <div class="avatar-row">
            <img :src="resolveAvatar(item.account.avatar_url, item.profile.real_name || item.account.username, 'mint')" :alt="item.profile.real_name || item.account.username" />
            <div>
              <strong>{{ item.profile.real_name || item.account.username }}</strong>
              <span>{{ item.profile.gender || '未设置' }} · {{ item.profile.age || '--' }} 岁 · {{ item.profile.city || '未设置城市' }}</span>
            </div>
          </div>

          <div class="action-row" style="margin-top: 12px;">
            <StatusBadge :label="`健康评分 ${item.health_score}`" :tone="healthScoreTone(item.health_score)" />
            <StatusBadge v-for="tag in item.tags.slice(0, 2)" :key="tag" :label="tag" tone="violet" />
          </div>
        </article>
      </div>
      <EmptyState v-else title="没有查到匹配患者" copy="可以清空搜索词，或从问诊详情页直接进入患者档案。" />
    </PanelCard>

    <PanelCard v-if="detail" title="患者档案" subtitle="历史病例并入档案视图，帮助医生建立连续性的长期判断。">
      <div v-loading="detailLoading">
        <div class="detail-grid">
          <article class="detail-card">
            <div class="avatar-row">
              <img :src="resolveAvatar(detail.account.avatar_url, detail.profile.real_name || detail.account.username, 'mint')" :alt="detail.profile.real_name || detail.account.username" />
              <div>
                <strong>{{ detail.profile.real_name || detail.account.username }}</strong>
                <span>{{ detail.profile.gender || '未设置' }} · {{ detail.profile.age || '--' }} 岁 · {{ detail.profile.city || '未设置城市' }}</span>
              </div>
            </div>
            <div class="action-row" style="margin-top: 14px;">
              <StatusBadge :label="`健康评分 ${detail.health_score}`" :tone="healthScoreTone(detail.health_score)" />
              <StatusBadge :label="detail.health_profile.skin_type || '未完善肤质'" tone="mint" />
              <StatusBadge :label="detail.health_profile.skin_sensitivity || '未完善敏感度'" tone="blue" />
            </div>
          </article>

          <article class="detail-card">
            <div class="tiny-label">长期健康信息</div>
            <div class="key-value" style="margin-top: 10px;">
              <div class="key-value__row">
                <span>过敏史</span>
                <strong>{{ allergyItems.join('、') || '无' }}</strong>
              </div>
              <div class="key-value__row">
                <span>既往史</span>
                <strong>{{ historyItems.join('、') || '无' }}</strong>
              </div>
              <div class="key-value__row">
                <span>长期用药</span>
                <strong>{{ medicationItems.join('、') || '无' }}</strong>
              </div>
              <div class="key-value__row">
                <span>生活习惯</span>
                <strong>{{ cleanVisibleText(detail.health_profile.sleep_pattern || detail.health_profile.diet_preference, '待完善') }}</strong>
              </div>
            </div>
          </article>
        </div>

        <div class="split-grid split-grid--wide" style="margin-top: 18px;">
          <PanelCard title="历史病例" subtitle="查看患者既往问诊、风险等级与医生处理状态。" compact>
            <div v-if="historyCases.length" class="list-panel">
              <article v-for="item in historyCases" :key="item.case_id" class="list-row" @click="openCase(item.case_id)">
                <div class="list-row__head">
                  <div>
                    <strong>{{ cleanVisibleText(item.summary_title, '待补充摘要') }}</strong>
                    <span>{{ item.case_no }} · {{ formatDateTime(item.submitted_at) }}</span>
                  </div>
                  <StatusBadge :label="statusLabel(item.status)" :tone="statusTone(item.status)" />
                </div>
                <p class="list-row__summary">{{ cleanVisibleText(item.chief_complaint, '患者未补充更多主诉。') }}</p>
                <div class="action-row" style="margin-top: 12px;">
                  <StatusBadge :label="riskLabel(item.risk_level)" :tone="riskTone(item.risk_level)" />
                </div>
              </article>
            </div>
            <EmptyState v-else title="暂无历史病例" copy="该患者最近还没有可回溯的问诊记录。" />
          </PanelCard>

          <PanelCard title="风险趋势" subtitle="结合病例次数与高风险占比，辅助长期随访判断。" compact>
            <TrendChart :points="detail.risk_trend" />
          </PanelCard>
        </div>

        <div class="split-grid split-grid--wide" style="margin-top: 18px;">
          <PanelCard title="长期护理建议" subtitle="汇总 AI 与医生建议，形成长期护理方向。" compact>
            <div v-if="careSuggestions.length" class="insight-stack">
              <article v-for="item in careSuggestions" :key="item" class="insight-card insight-card--single">
                <div class="insight-card__body">
                  <p class="insight-card__copy">{{ item }}</p>
                </div>
              </article>
            </div>
            <EmptyState v-else title="暂未沉淀护理建议" copy="随着历史病例累积，系统会逐步汇总更适合该患者的长期护理要点。" />
          </PanelCard>

          <PanelCard title="建议随访病例" subtitle="医生曾建议复查的病例会优先展示，便于持续跟进。" compact>
            <div v-if="detail.follow_up_cases.length" class="list-panel">
              <article v-for="item in detail.follow_up_cases" :key="item.case_id" class="list-row" @click="openCase(item.case_id)">
                <strong>{{ cleanVisibleText(item.summary_title, '复查病例') }}</strong>
                <p class="list-row__summary">{{ item.case_no }} · {{ item.reply_time }}</p>
              </article>
            </div>
            <EmptyState v-else title="暂无待随访病例" copy="当前患者还没有被标记为需要重点复查的历史问诊。" />
          </PanelCard>
        </div>
      </div>
    </PanelCard>

    <PanelCard v-else title="暂无患者档案" subtitle="当前筛选条件下没有可查看的患者资料。">
      <EmptyState title="没有可展示的患者档案" copy="先在左侧选择患者，或从问诊详情页直接打开对应档案。" />
    </PanelCard>
  </section>
</template>
