<script setup lang="ts">
import { onMounted, ref } from 'vue'

import MetricCard from '@/components/MetricCard.vue'
import PanelCard from '@/components/PanelCard.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import TrendChart from '@/components/TrendChart.vue'
import { getAdminWorkspace, getStageLabel } from '@/data/controlCenter'

const workspace = ref<Awaited<ReturnType<typeof getAdminWorkspace>> | null>(null)

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
      <PanelCard title="知识库流程总览" subtitle="上传 → 解析 → 切片 → 向量化 → 可检索，整个流程需要清晰高级而不拥挤。">
        <div class="process-flow">
          <article class="flow-step">
            <div class="eyebrow-pill">01</div>
            <strong>上传</strong>
            <span>{{ workspace.knowledgeDocuments.filter((item) => item.stage === 'UPLOADED').length }} 份待处理</span>
          </article>
          <article class="flow-step">
            <div class="eyebrow-pill">02</div>
            <strong>解析</strong>
            <span>{{ workspace.knowledgeDocuments.filter((item) => item.stage === 'PARSED').length }} 份处理中</span>
          </article>
          <article class="flow-step">
            <div class="eyebrow-pill">03</div>
            <strong>切片</strong>
            <span>{{ workspace.knowledgeDocuments.filter((item) => item.stage === 'CHUNKED').length }} 份已切片</span>
          </article>
          <article class="flow-step">
            <div class="eyebrow-pill">04</div>
            <strong>向量化</strong>
            <span>{{ workspace.knowledgeDocuments.filter((item) => item.stage === 'EMBEDDED').length }} 份待启用</span>
          </article>
          <article class="flow-step">
            <div class="eyebrow-pill">05</div>
            <strong>可检索</strong>
            <span>{{ workspace.knowledgeDocuments.filter((item) => item.stage === 'ENABLED').length }} 份已上线</span>
          </article>
        </div>
      </PanelCard>

      <PanelCard title="系统配置快照" subtitle="Prompt 版本、医生复核开关和上传限制从工作台直接看全。">
        <div class="key-value">
          <div v-for="item in workspace.configs" :key="item.config_key" class="key-value__row">
            <span>{{ item.title }}</span>
            <strong>{{ item.config_value }}</strong>
          </div>
        </div>
      </PanelCard>
    </section>

    <section class="split-grid">
      <PanelCard title="问诊趋势（近 7 天）" subtitle="数据运营感来自清晰的趋势表达，而不是堆满图表。">
        <TrendChart :points="workspace.trend" />
      </PanelCard>

      <PanelCard title="最新操作日志" subtitle="把系统动作、知识库处理和审核动作沉淀到同一个运营视角。">
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

      <PanelCard title="知识文档状态" subtitle="文档状态用标签和流程状态一起呈现，更符合产品化后台气质。">
        <div class="list-panel">
          <article v-for="item in workspace.knowledgeDocuments" :key="item.document_id" class="list-row">
            <div class="list-row__head">
              <div>
                <strong>{{ item.doc_title }}</strong>
                <p class="list-row__summary">{{ item.file_type }} · {{ item.file_size }} · {{ item.uploaded_at }}</p>
              </div>
              <StatusBadge :label="getStageLabel(item.stage)" tone="violet" />
            </div>
          </article>
        </div>
      </PanelCard>
    </section>
  </template>
</template>
