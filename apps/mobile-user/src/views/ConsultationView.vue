<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import DirectionBars from '../components/DirectionBars.vue'
import RiskBadge from '../components/RiskBadge.vue'
import { uploadImage } from '../services/api'
import { createConsultation } from '../services/consultation'

type UploadEntry = {
  id: string
  file: File
  url: string
  name: string
}

const router = useRouter()
const fileInputRef = ref<HTMLInputElement | null>(null)
const loading = ref(false)
const errorMessage = ref('')
const uploads = ref<UploadEntry[]>([])
const activeUploadId = ref('')

const form = reactive({
  description: '',
  onsetDuration: '2 天内',
  itchLevel: 3,
  painLevel: 1,
  spreadFlag: false,
  spreadParts: ['面部'] as string[],
})

const lowerDescription = computed(() => form.description.toLowerCase())
const activeUploadIndex = computed(() => {
  const index = uploads.value.findIndex((item) => item.id === activeUploadId.value)
  return index === -1 ? 0 : index
})
const activeUpload = computed(() => uploads.value[activeUploadIndex.value] ?? null)
const canAddMore = computed(() => uploads.value.length < 5)

const directionPreview = computed(() => [
  { label: '接触性皮炎', value: lowerDescription.value.includes('itch') || form.description.includes('痒') ? 28 : 45 },
  { label: '湿疹样反应', value: form.spreadFlag ? 32 : 20 },
  { label: '屏障受损', value: lowerDescription.value.includes('dry') || form.description.includes('干') ? 42 : 15 },
  { label: '痤疮相关变化', value: lowerDescription.value.includes('pimple') || form.description.includes('痘') ? 30 : 10 },
])

function createUploadEntry(file: File): UploadEntry {
  return {
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    file,
    url: URL.createObjectURL(file),
    name: file.name,
  }
}

function revokeUpload(entry: UploadEntry) {
  if (entry.url.startsWith('blob:')) {
    URL.revokeObjectURL(entry.url)
  }
}

function revokeAllUploads() {
  uploads.value.forEach(revokeUpload)
}

function openPicker() {
  fileInputRef.value?.click()
}

function handleFiles(event: Event) {
  const target = event.target as HTMLInputElement
  const selectedFiles = Array.from(target.files || [])
  const room = 5 - uploads.value.length

  if (!selectedFiles.length) {
    return
  }

  if (room <= 0) {
    errorMessage.value = '最多上传 5 张图片，可先删除后再补充。'
    target.value = ''
    return
  }

  const acceptedFiles = selectedFiles.slice(0, room)
  const nextEntries = acceptedFiles.map(createUploadEntry)
  uploads.value = [...uploads.value, ...nextEntries]
  activeUploadId.value = nextEntries[nextEntries.length - 1]?.id || uploads.value[0]?.id || ''

  if (selectedFiles.length > room) {
    errorMessage.value = '最多保留 5 张图片，已自动忽略超出部分。'
  } else {
    errorMessage.value = ''
  }

  target.value = ''
}

function removeUpload(id: string) {
  const index = uploads.value.findIndex((item) => item.id === id)
  if (index === -1) return

  revokeUpload(uploads.value[index])
  uploads.value = uploads.value.filter((item) => item.id !== id)

  if (!uploads.value.length) {
    activeUploadId.value = ''
    return
  }

  if (activeUploadId.value === id) {
    const nextIndex = Math.min(index, uploads.value.length - 1)
    activeUploadId.value = uploads.value[nextIndex].id
  }
}

function toggleSpreadPart(part: string) {
  if (form.spreadParts.includes(part)) {
    form.spreadParts = form.spreadParts.filter((item) => item !== part)
  } else {
    form.spreadParts = [...form.spreadParts, part]
  }
}

async function submit() {
  if (!uploads.value.length) {
    errorMessage.value = '请至少上传 1 张图片。'
    return
  }

  if (!form.description.trim()) {
    errorMessage.value = '请先填写症状描述。'
    return
  }

  try {
    loading.value = true
    errorMessage.value = ''

    const uploadedImages = await Promise.all(uploads.value.map((item) => uploadImage(item.file)))
    const result = await createConsultation({
      chief_complaint: form.description.trim(),
      onset_duration: form.onsetDuration,
      itch_level: Number(form.itchLevel),
      pain_level: Number(form.painLevel),
      spread_flag: form.spreadFlag ? 1 : 0,
      need_doctor_review: 0,
      image_urls: uploadedImages.map((item) => item.file_url),
    })

    router.push(`/analysis/${result.consultation.case_id}`)
  } catch (error) {
    errorMessage.value = (error as Error).message
  } finally {
    loading.value = false
  }
}

onBeforeUnmount(() => {
  revokeAllUploads()
})
</script>

<template>
  <section class="analysis-layout">
    <article class="surface-card">
      <div class="section-head">
        <div>
          <p class="section-eyebrow">步骤 1</p>
          <h1 class="section-title">上传图片并补充症状</h1>
          <p class="section-subtitle">先确认图片清晰度，再补充症状和时长，这一套结构后续也更方便迁移到小程序。</p>
        </div>
      </div>

      <div class="page-stack">
        <div class="field">
          <label>皮肤图片（最多 5 张）</label>
          <input
            ref="fileInputRef"
            class="upload-picker__input"
            type="file"
            accept="image/*"
            multiple
            @change="handleFiles"
          />

          <button type="button" class="upload-picker__hero" @click="openPicker">
            <span class="upload-picker__icon">↑</span>
            <div class="upload-picker__hero-copy">
              <strong>{{ uploads.length ? '继续补充图片' : '上传皮肤图片' }}</strong>
              <p>{{ uploads.length ? `当前已上传 ${uploads.length} 张，可继续补充不同角度。` : '支持 JPG、PNG、WebP，建议上传正面、侧面和局部特写。' }}</p>
              <span class="upload-picker__hint">图片会尽量完整显示，方便在提交前确认全貌。</span>
            </div>
          </button>

          <div v-if="activeUpload" class="upload-stage">
            <div class="upload-stage__preview">
              <img class="upload-stage__image" :src="activeUpload.url" :alt="activeUpload.name" />
            </div>

            <div class="upload-stage__toolbar">
              <div>
                <strong>{{ activeUpload.name }}</strong>
                <p>第 {{ activeUploadIndex + 1 }} 张，共 {{ uploads.length }} 张。建议补充不同角度，便于后续判断。</p>
              </div>
              <button v-if="canAddMore" type="button" class="ghost-button" @click="openPicker">继续添加</button>
            </div>

            <div class="upload-stage__thumbs">
              <article v-for="(item, index) in uploads" :key="item.id" class="upload-thumb-card">
                <button
                  type="button"
                  class="upload-thumb-card__preview"
                  :class="{ 'is-active': item.id === activeUploadId }"
                  @click="activeUploadId = item.id"
                >
                  <img :src="item.url" :alt="`上传图片 ${index + 1}`" />
                  <span class="upload-thumb-card__index">{{ String(index + 1).padStart(2, '0') }}</span>
                </button>
                <button type="button" class="upload-thumb-card__remove" @click="removeUpload(item.id)">删除</button>
              </article>
            </div>
          </div>
        </div>

        <div class="field">
          <label>症状描述</label>
          <textarea
            v-model="form.description"
            class="ghost-textarea"
            maxlength="300"
            placeholder="例如：面部泛红伴瘙痒，清洁后更明显，鼻翼周围有轻微刺痛。"
          />
        </div>

        <div class="grid-2">
          <div class="field">
            <label>发病时长</label>
            <select v-model="form.onsetDuration" class="ghost-select">
              <option>今天</option>
              <option>2 天内</option>
              <option>3 天内</option>
              <option>1 周内</option>
              <option>1 个月内</option>
            </select>
          </div>
          <div class="field">
            <label>是否扩散</label>
            <div class="segment">
              <button type="button" :class="{ 'is-active': !form.spreadFlag }" @click="form.spreadFlag = false">否</button>
              <button type="button" :class="{ 'is-active': form.spreadFlag }" @click="form.spreadFlag = true">是</button>
            </div>
          </div>
        </div>

        <div class="grid-2">
          <div class="field">
            <label>瘙痒程度 {{ form.itchLevel }}</label>
            <input v-model="form.itchLevel" class="ghost-input" type="range" min="0" max="5" />
          </div>
          <div class="field">
            <label>疼痛程度 {{ form.painLevel }}</label>
            <input v-model="form.painLevel" class="ghost-input" type="range" min="0" max="5" />
          </div>
        </div>

        <div class="field">
          <label>扩散部位（可多选）</label>
          <div class="action-row">
            <button
              v-for="item in ['面部', '颈部', '手臂', '躯干', '其他']"
              :key="item"
              type="button"
              class="ghost-button"
              @click="toggleSpreadPart(item)"
            >
              <span :style="{ color: form.spreadParts.includes(item) ? '#173d89' : '#4e638f' }">{{ item }}</span>
            </button>
          </div>
        </div>

        <button type="button" class="primary-button" :disabled="loading" @click="submit">
          {{ loading ? '正在上传图片并生成智能结果...' : '提交问诊' }}
        </button>
        <p v-if="errorMessage" class="card-copy" style="color: #d74f68;">{{ errorMessage }}</p>
      </div>
    </article>

    <article class="surface-card">
      <div class="section-head">
        <div>
          <p class="section-eyebrow">步骤 2</p>
          <h2 class="card-title">提交前说明</h2>
        </div>
        <RiskBadge :label="form.spreadFlag || form.painLevel >= 4 ? '中高风险' : '中低风险'" :tone="form.spreadFlag || form.painLevel >= 4 ? 'amber' : 'mint'" />
      </div>
      <p class="card-copy">
        后端会把本地上传的图片转换成 Base64 Data URL，再发送给视觉模型。这样即使当前是 H5 调试，也能和后续小程序共用同一条真实分析链路。
      </p>
      <div class="surface-card surface-card--compact" style="margin-top: 18px;">
        <p class="section-eyebrow">方向预估预览</p>
        <DirectionBars :items="directionPreview" />
      </div>
      <div class="surface-card surface-card--compact" style="margin-top: 18px;">
        <p class="section-eyebrow">处理规则</p>
        <div class="timeline-list" style="margin-top: 12px;">
          <article class="timeline-item">
            <strong>真实图文分析</strong>
            <p>页面会上传真实图片、创建真实问诊记录，并直接展示后端保存的结构化分析结果。</p>
          </article>
          <article class="timeline-item">
            <strong>高风险自动复核</strong>
            <p>如果模型判断为高风险，系统会按业务规则自动推进到医生复核流程。</p>
          </article>
        </div>
      </div>
    </article>

    <article class="surface-card">
      <div class="section-head">
        <div>
          <p class="section-eyebrow">步骤 3</p>
          <h2 class="card-title">提交后会发生什么</h2>
        </div>
      </div>
      <div class="timeline-list">
        <article class="timeline-item">
          <strong>自动跳转分析页</strong>
          <p>提交成功后，页面会根据后端返回的病例 ID 自动打开对应的分析详情页。</p>
        </article>
        <article class="timeline-item">
          <strong>历史记录同步</strong>
          <p>同一条问诊记录会同步出现在分析页和历史记录页，不再依赖本地演示数据。</p>
        </article>
        <article class="timeline-item">
          <strong>结果仅做辅助</strong>
          <p>智能结果仅用于辅助分诊和健康建议，不替代线下医生诊断。</p>
        </article>
      </div>
    </article>
  </section>
</template>
