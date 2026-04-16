<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { request } from '../services/api'

const route = useRoute()
const router = useRouter()
const detail = ref<any>(null)

async function loadData() {
  detail.value = await request(`/consultations/${route.params.caseId}`)
}

onMounted(loadData)
</script>

<template>
  <section class="screen">
    <div class="screen-head">
      <h1 class="screen-title">AI 分析结果</h1>
      <p class="screen-subtitle">{{ detail?.case_no }} · {{ detail?.summary_title }}</p>
    </div>

    <div v-if="detail" class="card">
      <div class="chip-row">
        <span class="chip">{{ detail.status }}</span>
        <span class="chip" :class="{ 'chip-danger': detail.risk_level === 'HIGH' }">风险 {{ detail.risk_level || '-' }}</span>
      </div>

      <div class="grid-2" style="margin-top: 14px;">
        <div class="stat-box">
          <div class="stat-label">瘙痒</div>
          <div class="stat-value">{{ detail.itch_level }}</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">疼痛</div>
          <div class="stat-value">{{ detail.pain_level }}</div>
        </div>
      </div>

      <div v-if="detail.images?.length" class="image-grid" style="margin-top: 14px;">
        <img v-for="image in detail.images" :key="image.image_id" :src="image.file_url" :alt="image.file_name" />
      </div>
    </div>

    <div class="card">
      <div class="list-title">图像观察</div>
      <div class="list-meta">{{ detail?.ai_result?.image_observation }}</div>
    </div>

    <div class="card">
      <div class="list-title">可能方向</div>
      <div class="list-meta">{{ detail?.ai_result?.possible_conditions }}</div>
    </div>

    <div class="card">
      <div class="list-title">护理建议</div>
      <div class="list-meta">{{ detail?.ai_result?.care_advice }}</div>
    </div>

    <div class="card">
      <div class="list-title">高风险提醒</div>
      <p class="notice">{{ detail?.ai_result?.high_risk_alert }}</p>
      <div class="list-meta">{{ detail?.ai_result?.disclaimer }}</div>
    </div>

    <div v-if="detail?.doctor_reply" class="card">
      <div class="list-title">医生回复</div>
      <div class="list-meta" style="margin-top: 10px;">{{ detail.doctor_reply.doctor_name }} · {{ detail.doctor_reply.created_at }}</div>
      <p style="line-height: 1.8;">{{ detail.doctor_reply.content }}</p>
    </div>

    <div class="grid-2">
      <button class="btn btn-secondary" @click="router.push('/history')">查看历史</button>
      <button class="btn btn-primary" @click="router.push('/qa')">继续问答</button>
    </div>
  </section>
</template>

