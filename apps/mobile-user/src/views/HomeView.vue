<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { request } from '../services/api'
import { getSession } from '../services/session'

const router = useRouter()
const dashboard = ref<any>(null)
const announcements = ref<any[]>([])

async function loadData() {
  dashboard.value = await request('/user/dashboard')
  announcements.value = await request('/announcements')
}

onMounted(loadData)
</script>

<template>
  <section class="screen">
    <div class="screen-head">
      <p class="pill">欢迎回来</p>
      <h1 class="screen-title">{{ dashboard?.profile?.real_name || getSession()?.profile?.real_name || '皮肤健康用户' }}</h1>
      <p class="screen-subtitle">今天也让皮肤状态更稳定一些，先看下最近的关注点。</p>
    </div>

    <div class="card">
      <div class="grid-2">
        <div class="stat-box">
          <div class="stat-label">问诊总量</div>
          <div class="stat-value">{{ dashboard?.summary?.consultation_total || 0 }}</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">待处理</div>
          <div class="stat-value">{{ dashboard?.summary?.waiting_total || 0 }}</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">医生已回复</div>
          <div class="stat-value">{{ dashboard?.summary?.doctor_replied_total || 0 }}</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">未读通知</div>
          <div class="stat-value">{{ dashboard?.summary?.unread_notifications || 0 }}</div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="grid-3">
        <button class="btn btn-primary" @click="router.push('/consultation')">发起图文问诊</button>
        <button class="btn btn-secondary" @click="router.push('/qa')">知识问答</button>
        <button class="btn btn-secondary" @click="router.push('/health')">健康档案</button>
      </div>
    </div>

    <div v-if="dashboard?.current_focus" class="card">
      <div class="stat-label">当前关注</div>
      <div class="list-title" style="margin-top: 10px;">{{ dashboard.current_focus.summary_title }}</div>
      <div class="list-meta">{{ dashboard.current_focus.case_no }} · {{ dashboard.current_focus.status }} · {{ dashboard.current_focus.risk_level }}</div>
      <button class="btn btn-primary" style="margin-top: 14px; width: 100%;" @click="router.push(`/analysis/${dashboard.current_focus.case_id}`)">
        查看分析结果
      </button>
    </div>

    <div class="card">
      <div class="screen-title" style="font-size: 22px;">最近问诊</div>
      <div class="list" style="margin-top: 14px;">
        <article v-for="item in dashboard?.recent_cases || []" :key="item.case_id" class="list-item" @click="router.push(`/analysis/${item.case_id}`)">
          <div class="list-title">{{ item.summary_title }}</div>
          <div class="list-meta">{{ item.case_no }} · {{ item.status }} · 风险 {{ item.risk_level || '-' }}</div>
        </article>
      </div>
    </div>

    <div class="card">
      <div class="screen-title" style="font-size: 22px;">平台公告</div>
      <div class="list" style="margin-top: 14px;">
        <article v-for="item in announcements.slice(0, 3)" :key="item.announcement_id" class="list-item">
          <div class="list-title">{{ item.title }}</div>
          <div class="list-meta">{{ item.content }}</div>
        </article>
      </div>
    </div>
  </section>
</template>

