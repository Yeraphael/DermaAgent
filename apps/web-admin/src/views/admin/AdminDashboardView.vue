<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'

import MetricCard from '@/components/MetricCard.vue'
import EmptyState from '@/components/EmptyState.vue'
import PanelCard from '@/components/PanelCard.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import TrendChart from '@/components/TrendChart.vue'
import { auditAdminDoctor, fetchAdminDashboard, type AdminDashboard } from '@/api/workspace'
import { auditStatusLabel, auditStatusTone, cleanVisibleText, resolveAvatar, serviceStatusLabel, serviceStatusTone } from '@/utils/workspace'

const router = useRouter()
const loading = ref(false)
const dashboard = ref<AdminDashboard | null>(null)

async function loadDashboard() {
  try {
    loading.value = true
    dashboard.value = await fetchAdminDashboard()
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    loading.value = false
  }
}

async function quickAudit(doctorId: number, auditStatus: string) {
  try {
    await auditAdminDoctor(doctorId, { audit_status: auditStatus })
    ElMessage.success('审核状态已更新。')
    await loadDashboard()
  } catch (error) {
    ElMessage.error((error as Error).message)
  }
}

function openDoctor(doctorId: number) {
  router.push(`/admin/doctors/${doctorId}`)
}

function openConsultations() {
  router.push('/admin/consultations')
}

onMounted(loadDashboard)
</script>

<template>
  <div class="page-shell" v-loading="loading">
    <section v-if="dashboard" class="metric-grid metric-grid--six">
      <MetricCard label="用户总数" :value="dashboard.metrics.users_total" note="全平台普通用户账号总量。" accent="violet" />
      <MetricCard label="医生总数" :value="dashboard.metrics.doctors_total" note="包含待审核和服务中的医生账号。" accent="sky" />
      <MetricCard label="咨询总量" :value="dashboard.metrics.consultations_total" note="已提交的图文问诊累计数量。" accent="mint" />
      <MetricCard label="高风险咨询量" :value="dashboard.metrics.high_risk_total" note="需要重点监管与优先处理的病例。" accent="rose" />
      <MetricCard label="AI 调用次数" :value="dashboard.metrics.ai_calls_total" note="图文分析服务累计调用量。" accent="blue" />
      <MetricCard label="今日活跃医生" :value="dashboard.metrics.active_doctors_today" note="今日有实际处理行为的医生人数。" accent="lilac" />
    </section>

    <section v-if="dashboard" class="split-grid split-grid--wide">
      <PanelCard title="咨询趋势" subtitle="近 7 天咨询总量与高风险占比趋势。">
        <TrendChart :points="dashboard.trend" />
      </PanelCard>

      <PanelCard title="系统运行概览" subtitle="聚合查看模型状态、队列压力、平均响应时间与错误率。">
        <div class="metric-inline-grid">
          <article class="detail-card">
            <div class="tiny-label">模型状态</div>
            <strong>{{ dashboard.runtime.model_status === 'NORMAL' ? '正常' : '需关注' }}</strong>
            <p class="detail-copy">建议结合日志监控页持续观察异常波动。</p>
          </article>
          <article class="detail-card">
            <div class="tiny-label">队列状态</div>
            <strong>{{ dashboard.runtime.queue_waiting }} 条</strong>
            <p class="detail-copy">当前待医生处理问诊数量。</p>
          </article>
          <article class="detail-card">
            <div class="tiny-label">平均响应时间</div>
            <strong>{{ dashboard.runtime.avg_response_seconds || 0 }}s</strong>
            <p class="detail-copy">基于问诊提交到医生回复的平均耗时。</p>
          </article>
          <article class="detail-card">
            <div class="tiny-label">错误率</div>
            <strong>{{ dashboard.runtime.error_rate }}%</strong>
            <p class="detail-copy">来源于关键操作日志的异常比例。</p>
          </article>
        </div>
      </PanelCard>
    </section>

    <section v-if="dashboard" class="split-grid split-grid--wide">
      <PanelCard title="医生处理概览" subtitle="查看服务状态、审核状态、回复率与今日处理量。">
        <div v-if="dashboard.doctor_overview.length" class="list-panel">
          <article v-for="item in dashboard.doctor_overview" :key="item.doctor_id" class="list-row" @click="openDoctor(item.doctor_id)">
            <div class="list-row__head">
              <div class="avatar-row">
                <img :src="resolveAvatar(item.account.avatar_url, item.doctor_name)" :alt="item.doctor_name" />
                <div>
                  <strong>{{ item.doctor_name }}</strong>
                  <span>{{ item.department || '未设置科室' }} · {{ item.title_name || '未设置职称' }}</span>
                </div>
              </div>
              <div class="action-row">
                <StatusBadge :label="auditStatusLabel(item.audit_status)" :tone="auditStatusTone(item.audit_status)" />
                <StatusBadge :label="serviceStatusLabel(item.service_status)" :tone="serviceStatusTone(item.service_status)" />
              </div>
            </div>
            <div class="summary-grid">
              <div><span>回复率</span><strong>{{ item.response_rate }}%</strong></div>
              <div><span>今日处理</span><strong>{{ item.today_processed }}</strong></div>
            </div>
          </article>
        </div>
        <EmptyState v-else title="暂无医生处理数据" copy="医生开始处理问诊后，这里会显示关键运营指标。" />
      </PanelCard>

      <PanelCard title="待审核医生" subtitle="支持快速查看待审核医生，并直接完成通过或驳回。">
        <div v-if="dashboard.pending_doctors.length" class="list-panel">
          <article v-for="item in dashboard.pending_doctors" :key="item.doctor_id" class="list-row">
            <div class="list-row__head">
              <div>
                <strong>{{ item.doctor_name }}</strong>
                <span>{{ item.department || '未设置科室' }} · {{ item.title_name || '未设置职称' }}</span>
              </div>
              <StatusBadge label="待审核" tone="amber" />
            </div>
            <p class="list-row__summary">{{ item.hospital_name || '未完善执业机构' }} · {{ item.phone || '未填写联系电话' }}</p>
            <div class="action-row" style="margin-top: 12px;">
              <button type="button" class="soft-button" @click="quickAudit(item.doctor_id, 'APPROVED')">审核通过</button>
              <button type="button" class="ghost-button" @click="quickAudit(item.doctor_id, 'REJECTED')">驳回审核</button>
              <button type="button" class="ghost-button" @click="openDoctor(item.doctor_id)">查看详情</button>
            </div>
          </article>
        </div>
        <EmptyState v-else title="当前没有待审核医生" copy="新的医生入驻申请会在这里优先展示。" />
      </PanelCard>
    </section>

    <section v-if="dashboard" class="split-grid split-grid--wide">
      <PanelCard title="最新动态" subtitle="平台关键操作和业务变化会集中呈现。">
        <div v-if="dashboard.latest_activities.length" class="log-list">
          <article v-for="item in dashboard.latest_activities" :key="item.log_id" class="log-item">
            <strong>{{ cleanVisibleText(item.module_name) }} · {{ cleanVisibleText(item.operation_type) }}</strong>
            <p>{{ cleanVisibleText(item.operation_desc, '已记录关键操作。') }}</p>
            <span>{{ item.created_at }}</span>
          </article>
        </div>
        <EmptyState v-else title="暂无最新动态" copy="系统产生新的关键操作后，会在这里同步更新。" />
      </PanelCard>

      <PanelCard title="重点告警" subtitle="高风险问诊与系统异常会统一汇聚，便于快速决策。">
        <div v-if="dashboard.alerts.length" class="log-list">
          <article v-for="(item, index) in dashboard.alerts" :key="index" class="log-item">
            <strong>{{ cleanVisibleText(String(item.summary_title || item.type || '重点告警')) }}</strong>
            <p>
              {{ cleanVisibleText(String(item.patient_name || item.time || '系统已记录相关事件，可进入咨询记录或日志页继续查看。')) }}
            </p>
            <div class="action-row" style="margin-top: 12px;">
              <button type="button" class="ghost-button" @click="openConsultations">查看咨询记录</button>
            </div>
          </article>
        </div>
        <EmptyState v-else title="暂无重点告警" copy="当前没有需要升级处理的高优先级告警事件。" />
      </PanelCard>
    </section>
  </div>
</template>
