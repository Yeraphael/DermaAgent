<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { request, uploadImage } from '../services/api'

const router = useRouter()
const loading = ref(false)
const files = ref<File[]>([])
const previews = ref<string[]>([])
const form = reactive({
  chief_complaint: '',
  onset_duration: '3天',
  itch_level: 2,
  pain_level: 1,
  spread_flag: 0,
  need_doctor_review: 1,
})

function handleFiles(event: Event) {
  const target = event.target as HTMLInputElement
  const selected = Array.from(target.files || []).slice(0, 3)
  files.value = selected
  previews.value = selected.map((file) => URL.createObjectURL(file))
}

async function submit() {
  if (!form.chief_complaint.trim()) {
    alert('请先填写症状描述')
    return
  }
  loading.value = true
  try {
    const imageUrls: string[] = []
    for (const file of files.value) {
      const uploaded = await uploadImage(file)
      imageUrls.push(uploaded.file_url)
    }
    const data = await request<any>('/consultations', {
      method: 'POST',
      data: {
        ...form,
        image_urls: imageUrls,
      },
    })
    router.push(`/analysis/${data.consultation.case_id}`)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="screen">
    <div class="screen-head">
      <h1 class="screen-title">图文问诊</h1>
      <p class="screen-subtitle">上传清晰皮肤图片并描述症状，提交后会立刻生成 AI 辅助分析结果。</p>
    </div>

    <div class="card">
      <div class="field">
        <label>症状描述</label>
        <textarea v-model="form.chief_complaint" class="textarea" placeholder="例如：脸颊发红发痒，换了护肤品后三天明显加重。"></textarea>
      </div>

      <div class="field" style="margin-top: 14px;">
        <label>起病时长</label>
        <select v-model="form.onset_duration" class="select">
          <option>3天</option>
          <option>1周</option>
          <option>2周</option>
          <option>1个月</option>
          <option>反复半年</option>
          <option>近三天明显加重</option>
        </select>
      </div>

      <div class="grid-2" style="margin-top: 14px;">
        <div class="field">
          <label>瘙痒程度 {{ form.itch_level }}</label>
          <input v-model="form.itch_level" class="input" type="range" min="0" max="5" />
        </div>
        <div class="field">
          <label>疼痛程度 {{ form.pain_level }}</label>
          <input v-model="form.pain_level" class="input" type="range" min="0" max="5" />
        </div>
      </div>

      <div class="chip-row" style="margin-top: 14px;">
        <button class="btn btn-secondary" @click="form.spread_flag = form.spread_flag ? 0 : 1">{{ form.spread_flag ? '已标记扩散' : '点击标记扩散' }}</button>
        <button class="btn btn-secondary" @click="form.need_doctor_review = form.need_doctor_review ? 0 : 1">{{ form.need_doctor_review ? '医生复核开启' : '仅看 AI 结果' }}</button>
      </div>

      <div class="field" style="margin-top: 14px;">
        <label>上传图片</label>
        <input class="input" type="file" accept="image/*" multiple @change="handleFiles" />
      </div>

      <div v-if="previews.length" class="image-grid" style="margin-top: 14px;">
        <img v-for="item in previews" :key="item" :src="item" alt="preview" />
      </div>

      <button class="btn btn-primary" style="width: 100%; margin-top: 16px;" :disabled="loading" @click="submit">
        {{ loading ? '正在上传并分析...' : '提交问诊并生成结果' }}
      </button>
    </div>
  </section>
</template>
