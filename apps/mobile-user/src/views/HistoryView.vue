<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { request } from '../services/api'

const router = useRouter()
const items = ref<any[]>([])

async function loadData() {
  const data = await request<any>('/consultations/my?page=1&page_size=30')
  items.value = data.list
}

onMounted(loadData)
</script>

<template>
  <section class="screen">
    <div class="screen-head">
      <h1 class="screen-title">问诊记录</h1>
      <p class="screen-subtitle">查看历史问诊、AI 分析状态和医生是否已回复。</p>
    </div>

    <div class="card">
      <div class="list">
        <article v-for="item in items" :key="item.case_id" class="list-item" @click="router.push(`/analysis/${item.case_id}`)">
          <div class="list-title">{{ item.summary_title }}</div>
          <div class="chip-row" style="margin-top: 10px;">
            <span class="chip">{{ item.status }}</span>
            <span class="chip" :class="{ 'chip-danger': item.risk_level === 'HIGH' }">风险 {{ item.risk_level || '-' }}</span>
            <span class="chip">{{ item.doctor_reply ? '医生已回复' : '等待医生协同' }}</span>
          </div>
          <div class="list-meta">{{ item.case_no }} · {{ item.submitted_at }}</div>
        </article>
      </div>
    </div>
  </section>
</template>

