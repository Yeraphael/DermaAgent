<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'

import EmptyState from '@/components/EmptyState.vue'
import MetricCard from '@/components/MetricCard.vue'
import PanelCard from '@/components/PanelCard.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import TrendChart from '@/components/TrendChart.vue'
import { fetchDoctorDashboard, type DoctorDashboard, type ConsultationDetail } from '@/api/workspace'
import { cleanVisibleText, formatPercent, resolveAvatar, riskLabel, riskTone, splitVisibleText, statusLabel, statusTone } from '@/utils/workspace'

const router = useRouter()
const loading = ref(false)
const dashboard = ref<DoctorDashboard | null>(null)

function openCase(item?: ConsultationDetail | null) {
  if (!item?.case_id) return
  router.push(`/doctor/consultations/${item.case_id}`)
}

function openPatient(item?: ConsultationDetail | null) {
  const userId = item?.patient?.account?.account_id
  if (!userId) return
  router.push(`/doctor/patients/${userId}`)
}

function riskBreakdown(item?: ConsultationDetail | null) {
  const names = item?.ai_result?.possible_conditions_list || splitVisibleText(item?.ai_result?.possible_conditions)
  const values = [45, 28, 17, 10]
  return names.slice(0, 4).map((label, index) => ({ label, value: values[index] || 10 }))
}

async function loadDashboard() {
  try {
    loading.value = true
    dashboard.value = await fetchDoctorDashboard()
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    loading.value = false
  }
}

onMounted(loadDashboard)
</script>

<template>
  <div class="page-shell" v-loading="loading">
    <section v-if="dashboard" class="metric-grid">
      <MetricCard label="待处理问诊" :value="dashboard.stats.pending_total" note="优先处理仍待医生回复的问诊单。" accent="violet" />
      <MetricCard label="今日已处理" :value="dashboard.stats.processed_today" note="按今日提交专业回复统计。" accent="sky" />
      <MetricCard label="高风险提醒" :value="dashboard.stats.high_risk_total" note="建议优先关注扩散、渗液、流脓等情况。" accent="rose" />
      <MetricCard label="AI 反馈准确率" :value="formatPercent(dashboard.stats.ai_feedback_accuracy)" note="基于医生对 AI 结果的反馈统计。" accent="mint" />
    </section>

    <section v-if="dashboard" class="split-grid split-grid--wide">
      <PanelCard title="优先处理队列" subtitle="把高风险、待处理和需要重点观察的问诊集中到同一视图。">
        <div v-if="dashboard.priority_queue.length" class="list-panel">
          <article
            v-for="item in dashboard.priority_queue"
            :key="item.case_id"
            class="list-row"
            @click="openCase(item)"
          >
            <div class="list-row__head">
              <div class="avatar-row">
                <img :src="resolveAvatar(item.patient?.account?.avatar_url, item.patient?.profile?.real_name || item.patient?.account?.username, 'mint')" :alt="item.patient?.profile?.real_name || '患者'" />
                <div>
                  <strong>{{ item.patient?.profile?.real_name || item.patient?.account?.username || '未命名患者' }}</strong>
                  <span>
                    {{ item.patient?.profile?.gender || '未设置' }} · {{ item.patient?.profile?.age || '--' }} 岁
                    · {{ item.submitted_at || '--' }}
                  </span>
                </div>
              </div>
              <StatusBadge :label="statusLabel(item.status)" :tone="statusTone(item.status)" />
            </div>

            <p class="list-row__summary">{{ cleanVisibleText(item.summary_title, '待补充摘要') }}</p>
            <div class="action-row" style="margin-top: 12px;">
              <StatusBadge :label="riskLabel(item.risk_level)" :tone="riskTone(item.risk_level)" />
              <StatusBadge
                v-for="tag in (item.patient?.tags || []).slice(0, 2)"
                :key="tag"
                :label="tag"
                tone="blue"
              />
            </div>
          </article>
        </div>
        <EmptyState v-else title="当前没有待处理问诊" copy="新的图文问诊进入队列后，会在这里优先展示。" />
      </PanelCard>

      <PanelCard title="今日焦点病例" subtitle="集中展示 AI 观察、风险等级与下一步处理重点。">
        <template v-if="dashboard.focus_case">
          <div class="detail-card">
            <div class="detail-row">
              <div>
                <div class="tiny-label">当前病例</div>
                <p class="detail-title">{{ dashboard.focus_case.case_no }}</p>
              </div>
              <StatusBadge :label="riskLabel(dashboard.focus_case.risk_level)" :tone="riskTone(dashboard.focus_case.risk_level)" />
            </div>
            <p class="detail-copy">{{ cleanVisibleText(dashboard.focus_case.ai_result?.image_observation, '系统正在整理图像观察要点。') }}</p>
          </div>

          <div class="progress-list" style="margin-top: 18px;">
            <div
              v-for="item in riskBreakdown(dashboard.focus_case)"
              :key="item.label"
              class="progress-item"
            >
              <span>{{ item.label }}</span>
              <div class="progress-track"><span :style="{ width: `${item.value}%` }" /></div>
              <strong>{{ item.value }}%</strong>
            </div>
          </div>

          <div class="action-row" style="margin-top: 18px;">
            <button type="button" class="primary-button" @click="openCase(dashboard.focus_case)">进入病例详情</button>
            <button type="button" class="ghost-button" @click="openPatient(dashboard.focus_case)">查看患者档案</button>
          </div>
        </template>
        <EmptyState v-else title="暂无焦点病例" copy="系统会优先推荐高风险或需要复核的病例。" />
      </PanelCard>
    </section>

    <section v-if="dashboard" class="split-grid split-grid--wide">
      <PanelCard title="医生效率趋势" subtitle="同步查看最近 7 天处理量和高风险问诊变化。">
        <TrendChart :points="dashboard.trend" />
      </PanelCard>

      <PanelCard title="高风险提醒" subtitle="建议优先线下就医或需要重点复查的病例会收口在这里。">
        <div v-if="dashboard.high_risk_alerts.length" class="log-list">
          <article v-for="item in dashboard.high_risk_alerts" :key="item.case_id" class="log-item">
            <strong>{{ cleanVisibleText(item.summary_title, '高风险问诊') }}</strong>
            <p>{{ cleanVisibleText(item.alert, '当前病例存在较明显风险信号，建议尽快处理并关注线下面诊建议。') }}</p>
            <div class="action-row" style="margin-top: 12px;">
              <StatusBadge :label="item.patient?.profile?.real_name || item.patient?.account?.username || '患者'" tone="slate" />
              <StatusBadge :label="item.case_no" tone="blue" />
              <StatusBadge :label="riskLabel(item.risk_level)" :tone="riskTone(item.risk_level)" />
            </div>
          </article>
        </div>
        <EmptyState v-else title="暂无高风险提醒" copy="当前没有需要优先升级处理的高风险病例。" />
      </PanelCard>
    </section>
  </div>
</template>
