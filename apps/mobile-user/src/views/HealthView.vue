<script setup lang="ts">
import { onMounted, reactive } from 'vue'

import { request } from '../services/api'

const form = reactive({
  allergy_history: '',
  past_medical_history: '',
  medication_history: '',
  skin_type: '',
  skin_sensitivity: '',
  sleep_pattern: '',
  diet_preference: '',
  special_notes: '',
})

async function loadData() {
  const data = await request<any>('/user/health-profile')
  Object.assign(form, data)
}

async function save() {
  await request('/user/health-profile', {
    method: 'PUT',
    data: form,
  })
  alert('健康档案已保存')
}

onMounted(loadData)
</script>

<template>
  <section class="screen">
    <div class="screen-head">
      <h1 class="screen-title">健康档案</h1>
      <p class="screen-subtitle">完善你的过敏史、肤质、生活习惯，便于 AI 和医生更准确理解皮肤状态。</p>
    </div>

    <div class="card">
      <div class="field"><label>过敏史</label><textarea v-model="form.allergy_history" class="textarea"></textarea></div>
      <div class="field" style="margin-top: 12px;"><label>既往病史</label><textarea v-model="form.past_medical_history" class="textarea"></textarea></div>
      <div class="field" style="margin-top: 12px;"><label>近期用药</label><textarea v-model="form.medication_history" class="textarea"></textarea></div>
      <div class="field" style="margin-top: 12px;"><label>肤质</label><input v-model="form.skin_type" class="input" /></div>
      <div class="field" style="margin-top: 12px;"><label>敏感程度</label><input v-model="form.skin_sensitivity" class="input" /></div>
      <div class="field" style="margin-top: 12px;"><label>睡眠情况</label><input v-model="form.sleep_pattern" class="input" /></div>
      <div class="field" style="margin-top: 12px;"><label>饮食偏好</label><input v-model="form.diet_preference" class="input" /></div>
      <div class="field" style="margin-top: 12px;"><label>备注</label><textarea v-model="form.special_notes" class="textarea"></textarea></div>
      <button class="btn btn-primary" style="width: 100%; margin-top: 16px;" @click="save">保存健康档案</button>
    </div>
  </section>
</template>
