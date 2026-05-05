<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import EmptyState from '@/components/EmptyState.vue'
import MetricCard from '@/components/MetricCard.vue'
import PanelCard from '@/components/PanelCard.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import TrendChart from '@/components/TrendChart.vue'
import { fetchAdminLogsOverview, type LogsOverview } from '@/api/workspace'
import { cleanVisibleText } from '@/utils/workspace'

const loading = ref(false)
const keyword = ref('')
const category = ref<'ALL' | 'LOG' | 'AI' | 'ALERT'>('ALL')
const overview = ref<LogsOverview | null>(null)

const filteredLogs = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  return (overview.value?.recent_logs || []).filter((item) => {
    if (category.value !== 'ALL' && category.value !== 'LOG') return false
    const text = `${item.module_name} ${item.operation_type} ${item.operation_desc} ${item.role_type || ''}`.toLowerCase()
    return !query || text.includes(query)
  })
})

const filteredModelCalls = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  return (overview.value?.model_calls || []).filter((item) => {
    if (category.value !== 'ALL' && category.value !== 'AI') return false
    const text = `${item.model_name} ${item.analysis_status} ${item.fail_reason || ''}`.toLowerCase()
    return !query || text.includes(query)
  })
})

const filteredAlerts = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  return (overview.value?.alerts || []).filter((item) => {
    if (category.value !== 'ALL' && category.value !== 'ALERT') return false
    const text = `${item.title} ${item.content}`.toLowerCase()
    return !query || text.includes(query)
  })
})

async function loadOverview() {
  try {
    loading.value = true
    overview.value = await fetchAdminLogsOverview()
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    loading.value = false
  }
}

onMounted(loadOverview)
</script>

<template>
  <div class="page-shell" v-loading="loading">
    <section v-if="overview" class="metric-grid">
      <MetricCard label="登录日志" :value="overview.metrics.login_total" note="最近留痕的登录行为总量。" accent="violet" />
      <MetricCard label="操作日志" :value="overview.metrics.operation_total" note="关键业务与配置操作总量。" accent="sky" />
      <MetricCard label="AI 调用日志" :value="overview.metrics.ai_call_total" note="图文分析服务的调用记录总量。" accent="mint" />
      <MetricCard label="异常日志" :value="overview.metrics.error_total" note="关键链路中产生的异常事件数量。" accent="rose" />
    </section>

    <section class="split-grid split-grid--wide">
      <PanelCard title="运行趋势" subtitle="近 7 天日志总量与异常数量变化。">
        <TrendChart :points="overview?.trend || []" />
      </PanelCard>

      <PanelCard title="筛选条件" subtitle="按类别和关键字快速查看登录、操作、AI 调用与告警。">
        <div class="filters-grid filters-grid--triple">
          <div class="form-field">
            <label>关键字</label>
            <input
              v-model="keyword"
              class="ghost-input"
              placeholder="模块、操作描述、模型名、告警内容"
            />
          </div>
          <div class="form-field">
            <label>类别</label>
            <div class="segment">
              <button type="button" class="segment-button" :class="{ 'is-active': category === 'ALL' }" @click="category = 'ALL'">全部</button>
              <button type="button" class="segment-button" :class="{ 'is-active': category === 'LOG' }" @click="category = 'LOG'">操作日志</button>
              <button type="button" class="segment-button" :class="{ 'is-active': category === 'AI' }" @click="category = 'AI'">AI 调用</button>
              <button type="button" class="segment-button" :class="{ 'is-active': category === 'ALERT' }" @click="category = 'ALERT'">告警事件</button>
            </div>
          </div>
          <div class="action-row action-row--bottom">
            <button type="button" class="primary-button" @click="loadOverview">刷新日志</button>
          </div>
        </div>
      </PanelCard>
    </section>

    <section class="split-grid split-grid--wide">
      <PanelCard title="最新操作日志" subtitle="登录、管理操作、配置变更与接口处理统一留痕。">
        <div v-if="filteredLogs.length" class="log-list">
          <article v-for="item in filteredLogs" :key="item.log_id" class="log-item">
            <strong>{{ cleanVisibleText(item.module_name) }} · {{ cleanVisibleText(item.operation_type) }}</strong>
            <p>{{ cleanVisibleText(item.operation_desc, '已记录关键日志。') }}</p>
            <div class="action-row" style="margin-top: 12px;">
              <StatusBadge :label="item.role_type || '系统'" tone="blue" />
              <StatusBadge :label="item.operation_result || 'SUCCESS'" :tone="item.operation_result === 'SUCCESS' ? 'mint' : 'rose'" />
              <StatusBadge :label="item.request_ip || 'IP 未记录'" tone="slate" />
            </div>
            <span>{{ item.created_at }}</span>
          </article>
        </div>
        <EmptyState v-else title="暂无匹配日志" copy="可以调整筛选条件，或等待新的操作日志进入系统。" />
      </PanelCard>

      <PanelCard title="AI 调用日志" subtitle="查看模型调用状态、失败原因与相关问诊编号。">
        <div v-if="filteredModelCalls.length" class="log-list">
          <article v-for="item in filteredModelCalls" :key="item.record_id" class="log-item">
            <strong>{{ cleanVisibleText(item.model_name) }}</strong>
            <p>{{ cleanVisibleText(item.fail_reason, '本次调用已正常完成。') }}</p>
            <div class="action-row" style="margin-top: 12px;">
              <StatusBadge :label="`问诊 ${item.consultation_id}`" tone="slate" />
              <StatusBadge :label="item.analysis_status === 'SUCCESS' ? '成功' : '需关注'" :tone="item.analysis_status === 'SUCCESS' ? 'mint' : 'amber'" />
            </div>
            <span>{{ item.created_at }}</span>
          </article>
        </div>
        <EmptyState v-else title="暂无匹配 AI 日志" copy="当前筛选下没有可展示的 AI 调用记录。" />
      </PanelCard>
    </section>

    <section>
      <PanelCard title="告警事件" subtitle="聚合接口异常、模型失败和关键业务风险提示。">
        <div v-if="filteredAlerts.length" class="table-shell">
          <div class="table-head" style="--columns: 1fr 2fr 0.9fr;">
            <span>告警类型</span>
            <span>告警内容</span>
            <span>时间</span>
          </div>
          <div
            v-for="(item, index) in filteredAlerts"
            :key="`${item.time}-${index}`"
            class="table-row"
            style="--columns: 1fr 2fr 0.9fr;"
          >
            <div>
              <StatusBadge :label="cleanVisibleText(item.title, '告警事件')" tone="rose" />
            </div>
            <div>{{ cleanVisibleText(item.content, '系统已记录该告警事件。') }}</div>
            <div>{{ item.time }}</div>
          </div>
        </div>
        <EmptyState v-else title="暂无匹配告警" copy="当前筛选下没有需要重点关注的告警事件。" />
      </PanelCard>
    </section>
  </div>
</template>
