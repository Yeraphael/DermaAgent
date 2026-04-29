<script setup lang="ts">
import { onMounted, ref } from 'vue'

import MetricCard from '@/components/MetricCard.vue'
import PanelCard from '@/components/PanelCard.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { getAdminWorkspace } from '@/data/controlCenter'

const workspace = ref<Awaited<ReturnType<typeof getAdminWorkspace>> | null>(null)

async function loadWorkspace() {
  workspace.value = await getAdminWorkspace()
}

onMounted(loadWorkspace)
</script>

<template>
  <template v-if="workspace">
    <section class="metric-grid">
      <MetricCard label="今日操作日志" :value="workspace.operationLogs.length" note="管理员、系统和医生动作统一留痕" accent="sky" />
      <MetricCard label="模型调用记录" :value="workspace.modelLogs.length" note="图文问诊 / 文本直答 / 联网搜索统一观察" accent="mint" />
      <MetricCard label="成功率" value="96.3%" note="重试、失败和成功都可追踪" accent="violet" />
      <MetricCard label="平均响应" value="1.95s" note="服务端时延监控留出后续接真接口空间" accent="lilac" />
    </section>

    <section class="split-grid">
      <PanelCard title="操作日志" subtitle="面向管理员的关键操作记录。">
        <div class="log-list">
          <article v-for="item in workspace.operationLogs" :key="item.log_id" class="log-item">
            <strong>{{ item.module_name }} · {{ item.operation_type }}</strong>
            <p>{{ item.operation_desc }}</p>
            <div class="action-row" style="margin-top: 12px;">
              <StatusBadge :label="item.operator" tone="blue" />
              <StatusBadge :label="item.result" :tone="item.result === 'SUCCESS' ? 'mint' : 'rose'" />
            </div>
            <span>{{ item.created_at }}</span>
          </article>
        </div>
      </PanelCard>

      <PanelCard title="模型调用统计" subtitle="AI 调用次数、耗时和摘要让问题排查更有中台感。">
        <div class="log-list">
          <article v-for="item in workspace.modelLogs" :key="item.log_id" class="log-item">
            <strong>{{ item.biz_type }} · {{ item.model_name }}</strong>
            <p>{{ item.summary }}</p>
            <div class="action-row" style="margin-top: 12px;">
              <StatusBadge :label="item.duration" tone="blue" />
              <StatusBadge :label="`${item.token_cost} tokens`" tone="violet" />
              <StatusBadge :label="item.status" :tone="item.status === 'SUCCESS' ? 'mint' : item.status === 'RETRY' ? 'amber' : 'rose'" />
            </div>
            <span>{{ item.created_at }}</span>
          </article>
        </div>
      </PanelCard>
    </section>
  </template>
</template>
