<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'

import { request } from '../services/api'

const form = reactive({
  question: '痘痘反复长是不是和熬夜有关？',
})
const answer = ref<any>(null)
const history = ref<any[]>([])

async function loadHistory() {
  const data = await request<any>('/rag/qa/history?page=1&page_size=8')
  history.value = data.list
}

async function ask() {
  answer.value = await request('/rag/qa', {
    method: 'POST',
    data: { question: form.question },
  })
  await loadHistory()
}

onMounted(loadHistory)
</script>

<template>
  <section class="screen">
    <div class="screen-head">
      <h1 class="screen-title">皮肤健康问答</h1>
      <p class="screen-subtitle">基于知识库 mock 检索结果给出护理建议和风险提示。</p>
    </div>

    <div class="card">
      <div class="field">
        <label>输入问题</label>
        <textarea v-model="form.question" class="textarea"></textarea>
      </div>
      <div class="chip-row" style="margin-top: 12px;">
        <span class="chip" @click="form.question='痘痘反复长是不是和熬夜有关？'">痘痘与熬夜</span>
        <span class="chip" @click="form.question='脸上过敏泛红时可以继续刷酸吗？'">过敏与刷酸</span>
        <span class="chip" @click="form.question='湿疹反复瘙痒应该怎样护理？'">湿疹护理</span>
      </div>
      <button class="btn btn-primary" style="width: 100%; margin-top: 14px;" @click="ask">获取回答</button>
    </div>

    <div v-if="answer" class="card">
      <div class="list-title">AI 回答</div>
      <p style="line-height: 1.85;">{{ answer.answer }}</p>
      <p class="notice">{{ answer.risk_hint }}</p>
      <div class="list" style="margin-top: 12px;">
        <article v-for="item in answer.references" :key="item.chunk_id" class="list-item">
          <div class="list-title">{{ item.document_title }}</div>
          <div class="list-meta">{{ item.snippet }}</div>
        </article>
      </div>
    </div>

    <div class="card">
      <div class="list-title">最近问答</div>
      <div class="list" style="margin-top: 12px;">
        <article v-for="item in history" :key="item.qa_id" class="list-item">
          <div class="list-title">{{ item.question }}</div>
          <div class="list-meta">{{ item.answer }}</div>
        </article>
      </div>
    </div>
  </section>
</template>

