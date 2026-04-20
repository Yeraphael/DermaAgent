<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import PanelCard from '@/components/PanelCard.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { advanceKnowledgeDocument, getAdminWorkspace, getStageLabel, toggleKnowledgeEnabled } from '@/data/controlCenter'

const workspace = ref<Awaited<ReturnType<typeof getAdminWorkspace>> | null>(null)

async function loadWorkspace() {
  workspace.value = await getAdminWorkspace()
}

async function advance(documentId: number) {
  await advanceKnowledgeDocument(documentId)
  await loadWorkspace()
  ElMessage.success('文档流程已推进到下一阶段')
}

async function toggleEnabled(documentId: number) {
  await toggleKnowledgeEnabled(documentId)
  await loadWorkspace()
  ElMessage.success('文档启用状态已更新')
}

onMounted(loadWorkspace)
</script>

<template>
  <template v-if="workspace">
    <PanelCard title="知识库管理" subtitle="把“上传 → 解析 → 切片 → 向量化 → 可检索”做成真正有产品感的流程区。">
      <div class="process-flow">
        <article class="flow-step">
          <div class="eyebrow-pill">1</div>
          <strong>文档上传</strong>
          <span>支持 PDF / DOCX / ZIP</span>
        </article>
        <article class="flow-step">
          <div class="eyebrow-pill">2</div>
          <strong>自动解析</strong>
          <span>抽取结构化文本与元信息</span>
        </article>
        <article class="flow-step">
          <div class="eyebrow-pill">3</div>
          <strong>切片</strong>
          <span>控制 chunk 大小与召回效果</span>
        </article>
        <article class="flow-step">
          <div class="eyebrow-pill">4</div>
          <strong>向量化</strong>
          <span>嵌入向量库供 RAG 使用</span>
        </article>
        <article class="flow-step">
          <div class="eyebrow-pill">5</div>
          <strong>可检索</strong>
          <span>用户问答与医生辅助即时生效</span>
        </article>
      </div>
    </PanelCard>

    <section class="split-grid">
      <PanelCard title="文档列表" subtitle="每份文档都可以独立推进阶段、查看状态并启用。">
        <div class="list-panel">
          <article v-for="item in workspace.knowledgeDocuments" :key="item.document_id" class="list-row">
            <div class="list-row__head">
              <div>
                <strong>{{ item.doc_title }}</strong>
                <p class="list-row__summary">{{ item.category }} · {{ item.file_type }} · {{ item.file_size }} · Chunk {{ item.chunk_count }}</p>
              </div>
              <StatusBadge :label="getStageLabel(item.stage)" tone="violet" />
            </div>
            <div class="action-row" style="margin-top: 14px;">
              <button type="button" class="soft-button" @click="advance(item.document_id)">推进阶段</button>
              <button type="button" class="ghost-button" @click="toggleEnabled(item.document_id)">
                {{ item.enabled_flag === 1 ? '停用检索' : '启用检索' }}
              </button>
            </div>
          </article>
        </div>
      </PanelCard>

      <PanelCard title="流程说明" subtitle="让答辩展示时能一眼看出知识库的价值和可运营性。">
        <div class="log-list">
          <article class="log-item">
            <strong>上传阶段</strong>
            <p>支持临床指南、护理共识、FAQ 素材和医院内部流程文档。</p>
          </article>
          <article class="log-item">
            <strong>切片与向量化</strong>
            <p>切片后可控制召回粒度，向量化后为 RAG 问答与医生辅助检索提供底座。</p>
          </article>
          <article class="log-item">
            <strong>启用检索</strong>
            <p>开启后，用户端知识问答和医生回复推荐都会立即受到新文档影响。</p>
          </article>
        </div>
      </PanelCard>
    </section>
  </template>
</template>
