<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import RiskBadge from '../components/RiskBadge.vue'
import { askPortalQuestion, getPortalQaSnapshot } from '../shared/portal'

const form = reactive({
  question: '湿疹和过敏有什么区别？',
})
const answer = ref<Awaited<ReturnType<typeof askPortalQuestion>> | null>(null)
const snapshot = computed(() => getPortalQaSnapshot())

async function askQuestion() {
  if (!form.question.trim()) return
  answer.value = await askPortalQuestion(form.question)
}
</script>

<template>
  <section class="history-grid">
    <article class="surface-card">
      <div class="section-head">
        <div>
          <p class="section-eyebrow">知识问答</p>
          <h1 class="section-title">围绕护理知识做更安心的解释</h1>
          <p class="section-subtitle">除了问诊结果，用户端也需要一个可读、克制、全中文的护理问答入口。</p>
        </div>
      </div>

      <div class="field">
        <label>输入你的问题</label>
        <textarea v-model="form.question" class="ghost-textarea" maxlength="180" placeholder="例如：面部泛红时还能刷酸吗？" />
      </div>
      <div class="pill-row" style="margin-top: 14px;">
        <button
          v-for="item in snapshot.suggestions"
          :key="item"
          type="button"
          class="ghost-button"
          @click="form.question = item"
        >
          {{ item }}
        </button>
      </div>
      <button type="button" class="primary-button" style="margin-top: 18px;" @click="askQuestion">获取智能回答</button>

      <div v-if="answer" class="surface-card surface-card--compact" style="margin-top: 20px;">
        <div class="section-head">
          <div>
            <p class="section-eyebrow">智能回答</p>
            <h2 class="card-title">知识解释</h2>
          </div>
          <RiskBadge label="仅供参考" tone="blue" />
        </div>
        <p class="card-copy">{{ answer.answer }}</p>
        <p class="card-copy" style="margin-top: 14px;">参考来源：{{ answer.reference }}</p>
      </div>
    </article>

    <article class="surface-card">
      <div class="section-head">
        <div>
          <p class="section-eyebrow">最近问答</p>
          <h2 class="card-title">历史记录</h2>
        </div>
      </div>
      <div class="timeline-list">
        <article v-for="item in snapshot.history" :key="item.id" class="timeline-item">
          <strong>{{ item.question }}</strong>
          <p>{{ item.answer }}</p>
          <span>{{ item.createdAt }} · {{ item.reference }}</span>
        </article>
      </div>
    </article>
  </section>
</template>
