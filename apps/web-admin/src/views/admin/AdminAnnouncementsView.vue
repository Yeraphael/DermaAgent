<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import PanelCard from '@/components/PanelCard.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { getAdminWorkspace, publishAnnouncement } from '@/data/controlCenter'

const workspace = ref<Awaited<ReturnType<typeof getAdminWorkspace>> | null>(null)
const form = reactive({
  title: '',
  content: '',
  scope: 'ALL' as 'ALL' | 'DOCTOR' | 'USER',
})

async function loadWorkspace() {
  workspace.value = await getAdminWorkspace()
}

async function submitAnnouncement() {
  if (!form.title.trim() || !form.content.trim()) {
    ElMessage.warning('请填写完整公告标题和内容。')
    return
  }
  await publishAnnouncement({ ...form })
  form.title = ''
  form.content = ''
  form.scope = 'ALL'
  await loadWorkspace()
  ElMessage.success('公告已发布')
}

onMounted(loadWorkspace)
</script>

<template>
  <section class="split-grid">
    <PanelCard title="公告列表" subtitle="公告管理延续同一套轻盈卡片语言，用于医生端和用户端的运营触达。">
      <div class="log-list">
        <article v-for="item in workspace?.announcements || []" :key="item.announcement_id" class="announcement-card">
          <strong>{{ item.title }}</strong>
          <p>{{ item.content }}</p>
          <div class="action-row" style="margin-top: 12px;">
            <StatusBadge :label="item.scope" tone="violet" />
          </div>
          <span>{{ item.created_at }}</span>
        </article>
      </div>
    </PanelCard>

    <PanelCard title="发布新公告" subtitle="支持针对全员、医生或用户的定向消息。">
      <div class="doctor-response-grid">
        <div class="form-field">
          <label>公告标题</label>
          <input v-model="form.title" class="ghost-input" placeholder="例如：医生端高风险复核流程已升级" />
        </div>
        <div class="form-field">
          <label>公告对象</label>
          <div class="segment">
            <button type="button" class="segment-button" :class="{ 'is-active': form.scope === 'ALL' }" @click="form.scope = 'ALL'">全员</button>
            <button type="button" class="segment-button" :class="{ 'is-active': form.scope === 'DOCTOR' }" @click="form.scope = 'DOCTOR'">医生</button>
            <button type="button" class="segment-button" :class="{ 'is-active': form.scope === 'USER' }" @click="form.scope = 'USER'">用户</button>
          </div>
        </div>
        <div class="form-field">
          <label>公告内容</label>
          <textarea v-model="form.content" class="ghost-textarea" placeholder="请输入面向业务侧的公告内容…" />
        </div>
        <button type="button" class="primary-button" @click="submitAnnouncement">发布公告</button>
      </div>
    </PanelCard>
  </section>
</template>
