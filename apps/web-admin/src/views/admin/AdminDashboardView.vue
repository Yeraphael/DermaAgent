<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import MetricCard from '@/components/MetricCard.vue'
import PanelCard from '@/components/PanelCard.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import TrendChart from '@/components/TrendChart.vue'
import { getAdminWorkspace } from '@/data/controlCenter'

const workspace = ref<Awaited<ReturnType<typeof getAdminWorkspace>> | null>(null)

const qaInsights = computed(() => {
  if (!workspace.value) {
    return {
      direct: 0,
      web: 0,
      failed: 0,
    }
  }

  const modelLogs = workspace.value.modelLogs
  return {
    direct: modelLogs.filter((item) => item.biz_type === '文本直答').length,
    web: modelLogs.filter((item) => item.biz_type === '联网搜索问答').length,
    failed: modelLogs.filter((item) => item.status === 'FAILED').length,
  }
})

async function loadWorkspace() {
  workspace.value = await getAdminWorkspace()
}

onMounted(loadWorkspace)
</script>

<template>
  <template v-if="workspace">
    <section class="metric-grid" style="grid-template-columns: repeat(3, minmax(0, 1fr));">
      <MetricCard
        v-for="metric in workspace.metrics"
        :key="metric.label"
        :label="metric.label"
        :value="metric.value"
        :change="metric.change"
        :accent="metric.accent"
      />
    </section>

    <section class="split-grid">
      <PanelCard title="文本问答运行总览" subtitle="只保留轻量路由、直接回答、联网搜索和历史沉淀，后台也按这条主线观察。">
        <div class="process-flow">
          <article class="flow-step">
            <div class="eyebrow-pill">01</div>
            <strong>会话沉淀</strong>
            <span>{{ workspace.consultations.length + qaInsights.direct + qaInsights.web }} 条业务轨迹</span>
          </article>
          <article class="flow-step">
            <div class="eyebrow-pill">02</div>
            <strong>直接回答</strong>
            <span>{{ qaInsights.direct }} 次稳定命中</span>
          </article>
          <article class="flow-step">
            <div class="eyebrow-pill">03</div>
            <strong>联网搜索</strong>
            <span>{{ qaInsights.web }} 次调用 Tavily</span>
          </article>
          <article class="flow-step">
            <div class="eyebrow-pill">04</div>
            <strong>异常兜底</strong>
            <span>{{ qaInsights.failed }} 次需排查</span>
          </article>
        </div>
      </PanelCard>

      <PanelCard title="系统配置快照" subtitle="模型、医生复核开关和上传限制从工作台直接看全。">
        <div class="key-value">
          <div v-for="item in workspace.configs" :key="item.config_key" class="key-value__row">
            <span>{{ item.title }}</span>
            <strong>{{ item.config_value }}</strong>
          </div>
        </div>
      </PanelCard>
    </section>

    <section class="split-grid">
      <PanelCard title="问诊趋势（近 7 天）" subtitle="趋势图只保留最能说明业务状态的主线。">
        <TrendChart :points="workspace.trend" />
      </PanelCard>

      <PanelCard title="最新操作日志" subtitle="把会话、问诊、审核和系统动作放到同一个运营视角。">
        <div class="log-list">
          <article v-for="item in workspace.operationLogs.slice(0, 4)" :key="item.log_id" class="log-item">
            <strong>{{ item.module_name }} · {{ item.operation_type }}</strong>
            <p>{{ item.operation_desc }}</p>
            <span>{{ item.operator }} · {{ item.created_at }}</span>
          </article>
        </div>
      </PanelCard>
    </section>

    <section class="split-grid">
      <PanelCard title="医生管理预览" subtitle="待审核、已启用、已停用状态统一展示，不落回传统表格感。">
        <div class="list-panel">
          <article v-for="item in workspace.doctors.slice(0, 4)" :key="item.doctor_id" class="list-row">
            <div class="avatar-row">
              <img :src="item.avatar" :alt="item.doctor_name" />
              <div>
                <strong>{{ item.doctor_name }}</strong>
                <span>{{ item.hospital_name }} · {{ item.title_name }}</span>
              </div>
            </div>
            <div class="action-row" style="margin-top: 12px;">
              <StatusBadge :label="item.audit_status" tone="blue" />
              <StatusBadge :label="item.service_status === 1 ? '服务中' : '已暂停'" :tone="item.service_status === 1 ? 'mint' : 'slate'" />
            </div>
          </article>
        </div>
      </PanelCard>

      <PanelCard title="最近模型运行" subtitle="把图文分析、文本直答和联网搜索回答放到同一个观察面板。">
        <div class="list-panel">
          <article v-for="item in workspace.modelLogs.slice(0, 5)" :key="item.log_id" class="list-row">
            <div class="list-row__head">
              <div>
                <strong>{{ item.biz_type }}</strong>
                <p class="list-row__summary">{{ item.model_name }} · {{ item.duration }} · {{ item.created_at }}</p>
              </div>
              <StatusBadge :label="item.status" :tone="item.status === 'SUCCESS' ? 'mint' : item.status === 'RETRY' ? 'amber' : 'rose'" />
            </div>
            <p class="list-row__summary" style="margin-top: 12px;">{{ item.summary }}</p>
          </article>
        </div>
      </PanelCard>
    </section>
  </template>
</template>
