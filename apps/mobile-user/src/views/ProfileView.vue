<script setup lang="ts">
import { computed } from 'vue'

import RiskBadge from '../components/RiskBadge.vue'
import { getPortalProfile } from '../shared/portal'

const data = computed(() => getPortalProfile())
</script>

<template>
  <section class="page-stack">
    <article class="surface-card">
      <div class="section-head">
        <div>
          <p class="section-eyebrow">个人中心</p>
          <h1 class="section-title">{{ data.profile.real_name }}</h1>
          <p class="section-subtitle">{{ data.profile.city }} · {{ data.profile.age }} 岁 · {{ data.profile.skin_type }}</p>
        </div>
        <RiskBadge :label="data.profile.level" tone="violet" />
      </div>
      <div class="grid-3">
        <article class="metric-card">
          <span>皮肤类型</span>
          <strong>{{ data.healthArchive.skinType }}</strong>
        </article>
        <article class="metric-card">
          <span>最近医生</span>
          <strong>{{ data.healthArchive.latestDoctor }}</strong>
        </article>
        <article class="metric-card">
          <span>风险趋势</span>
          <strong>稳定</strong>
        </article>
      </div>
    </article>

    <div class="grid-2">
      <article class="surface-card">
        <div class="section-head">
          <div>
            <p class="section-eyebrow">护理计划</p>
            <h2 class="card-title">长期陪伴建议</h2>
          </div>
        </div>
        <div class="timeline-list">
          <article v-for="item in data.carePlan" :key="item" class="timeline-item">
            <strong>建议</strong>
            <p>{{ item }}</p>
          </article>
        </div>
      </article>

      <article class="surface-card">
        <div class="section-head">
          <div>
            <p class="section-eyebrow">偏好与档案</p>
            <h2 class="card-title">关键信息</h2>
          </div>
        </div>
        <div class="timeline-list">
          <article class="timeline-item">
            <strong>过敏项</strong>
            <p>{{ data.healthArchive.allergies.join('、') }}</p>
          </article>
          <article class="timeline-item">
            <strong>生活习惯</strong>
            <p>{{ data.healthArchive.habits.join('、') }}</p>
          </article>
        </div>
      </article>
    </div>
  </section>
</template>
