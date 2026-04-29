<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { uploadImage } from '../services/api'
import { createConsultation } from '../services/consultation'
import { buildConsultationNarrative, levelLabel, SYMPTOM_LEVELS } from '../utils/display'

type UploadEntry = {
  id: string
  file: File
  url: string
  name: string
}

const router = useRouter()

const fileInputRef = ref<HTMLInputElement | null>(null)
const dragOver = ref(false)
const submitting = ref(false)
const feedback = ref('')
const uploads = ref<UploadEntry[]>([])
const activeUploadId = ref('')

const onsetOptions = ['1 天内', '2 天内', '1 周内', '1 个月内', '超过 1 个月']
const spreadOptions = ['否', '是', '不确定']
const medicationOptions = ['否', '是', '不确定']
const bodyParts = ['面部', '头皮', '颈部', '躯干', '四肢', '私密部位', '其他']

const form = reactive({
  description: '',
  onsetDuration: '1 周内',
  spread: '否',
  itchLevel: 1,
  painLevel: 1,
  selectedParts: ['面部'] as string[],
  medication: '否',
})

const activeUpload = computed(() => uploads.value.find((item) => item.id === activeUploadId.value) || uploads.value[0] || null)
const canAddMore = computed(() => uploads.value.length < 5)
const descriptionCount = computed(() => form.description.trim().length)

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

function openPicker() {
  fileInputRef.value?.click()
}

function validateFile(file: File) {
  const accepted = ['image/jpeg', 'image/png', 'image/webp']
  if (!accepted.includes(file.type)) {
    return '仅支持 JPG、PNG、WebP 格式的图片。'
  }
  if (file.size > 10 * 1024 * 1024) {
    return '单张图片不能超过 10MB。'
  }
  return ''
}

function appendFiles(files: File[]) {
  if (!files.length) return
  const room = 5 - uploads.value.length
  if (room <= 0) {
    feedback.value = '最多上传 5 张图片，请先删除后再继续上传。'
    return
  }

  const acceptedFiles: File[] = []
  for (const file of files.slice(0, room)) {
    const error = validateFile(file)
    if (error) {
      feedback.value = error
      continue
    }
    acceptedFiles.push(file)
  }

  const nextEntries = acceptedFiles.map(createUploadEntry)
  uploads.value = [...uploads.value, ...nextEntries]
  if (nextEntries.length) {
    activeUploadId.value = nextEntries[nextEntries.length - 1].id
    feedback.value = ''
  }
}

function handleInputChange(event: Event) {
  const target = event.target as HTMLInputElement
  appendFiles(Array.from(target.files || []))
  target.value = ''
}

function handleDrop(event: DragEvent) {
  dragOver.value = false
  appendFiles(Array.from(event.dataTransfer?.files || []))
}

function removeUpload(id: string) {
  const current = uploads.value.find((item) => item.id === id)
  if (!current) return
  revokeUpload(current)
  uploads.value = uploads.value.filter((item) => item.id !== id)
  if (activeUploadId.value === id) {
    activeUploadId.value = uploads.value[0]?.id || ''
  }
}

function togglePart(part: string) {
  if (form.selectedParts.includes(part)) {
    form.selectedParts = form.selectedParts.filter((item) => item !== part)
    return
  }
  form.selectedParts = [...form.selectedParts, part]
}

async function submitConsultation() {
  if (!uploads.value.length) {
    feedback.value = '请至少上传 1 张皮肤图片。'
    return
  }
  if (!form.description.trim()) {
    feedback.value = '请详细描述您的症状。'
    return
  }
  if (descriptionCount.value > 300) {
    feedback.value = '症状描述不能超过 300 字。'
    return
  }

  try {
    submitting.value = true
    feedback.value = ''

    const uploadedImages = await Promise.all(uploads.value.map((item) => uploadImage(item.file)))
    const narrative = buildConsultationNarrative({
      description: form.description,
      onsetDuration: form.onsetDuration,
      spread: form.spread,
      itchLevel: levelLabel(form.itchLevel),
      painLevel: levelLabel(form.painLevel),
      areas: form.selectedParts,
      medication: form.medication,
    })

    const result = await createConsultation({
      chief_complaint: narrative,
      onset_duration: form.onsetDuration,
      itch_level: form.itchLevel,
      pain_level: form.painLevel,
      spread_flag: form.spread === '是' ? 1 : 0,
      need_doctor_review: form.spread === '是' || form.painLevel >= 3 || form.itchLevel >= 3 ? 1 : 0,
      image_urls: uploadedImages.map((item) => item.file_url),
    })

    router.push(`/analysis/${result.consultation.case_id}`)
  } catch (error) {
    feedback.value = (error as Error).message || '提交失败，请稍后重试。'
  } finally {
    submitting.value = false
  }
}

onBeforeUnmount(() => {
  uploads.value.forEach(revokeUpload)
})
</script>

<template>
  <section class="page-stack consultation-page">
    <article class="surface-card">
      <p class="section-eyebrow">图文问诊</p>
      <h1 class="section-title">上传皮肤图片并描述症状，医生将为您提供专业建议。</h1>
    </article>

    <div class="consult-layout">
      <article class="surface-card consult-form">
        <div class="field">
          <label>1. 上传皮肤图片</label>
          <p class="meta-copy">最多 5 张，支持 JPG、PNG、WebP，单张不超过 10MB</p>

          <input
            ref="fileInputRef"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            multiple
            class="consult-file-input"
            @change="handleInputChange"
          />

          <button
            type="button"
            class="upload-panel"
            :class="{ 'is-drag-over': dragOver }"
            @click="openPicker"
            @dragover.prevent="dragOver = true"
            @dragleave.prevent="dragOver = false"
            @drop.prevent="handleDrop"
          >
            <strong>点击或拖拽图片到此处上传</strong>
            <span>支持 JPG、PNG、WebP，单张不超过 10MB</span>
          </button>

          <div v-if="uploads.length" class="upload-preview">
            <div v-if="activeUpload" class="upload-preview__main">
              <img :src="activeUpload.url" :alt="activeUpload.name" />
            </div>

            <div class="upload-preview__list">
              <article v-for="item in uploads" :key="item.id" class="upload-preview__item">
                <button
                  type="button"
                  class="upload-preview__thumb"
                  :class="{ 'is-active': activeUploadId === item.id }"
                  @click="activeUploadId = item.id"
                >
                  <img :src="item.url" :alt="item.name" />
                </button>
                <button type="button" class="text-button upload-preview__remove" @click="removeUpload(item.id)">删除</button>
              </article>

              <button v-if="canAddMore" type="button" class="upload-preview__more" @click="openPicker">
                继续上传
              </button>
            </div>
          </div>
        </div>

        <div class="field">
          <label>2. 症状描述</label>
          <textarea
            v-model="form.description"
            class="ghost-textarea"
            maxlength="300"
            placeholder="请详细描述您的症状，如出现时间、部位、颜色、形态、伴随感受等..."
          />
          <p class="meta-copy textarea-counter">{{ descriptionCount }}/300</p>
        </div>

        <div class="field-grid">
          <div class="field">
            <label>3. 发病时长</label>
            <select v-model="form.onsetDuration" class="ghost-select">
              <option v-for="item in onsetOptions" :key="item" :value="item">{{ item }}</option>
            </select>
          </div>

          <div class="field">
            <label>4. 是否扩散</label>
            <div class="choice-group">
              <button
                v-for="item in spreadOptions"
                :key="item"
                type="button"
                :class="{ 'is-active': form.spread === item }"
                @click="form.spread = item"
              >
                {{ item }}
              </button>
            </div>
          </div>
        </div>

        <div class="field-grid">
          <div class="field">
            <label>5. 瘙痒程度</label>
            <div class="slider-card">
              <input v-model.number="form.itchLevel" class="slider-card__input" type="range" min="0" max="4" step="1" />
              <div class="slider-card__labels">
                <span v-for="item in SYMPTOM_LEVELS" :key="item">{{ item }}</span>
              </div>
              <strong>{{ levelLabel(form.itchLevel) }}</strong>
            </div>
          </div>

          <div class="field">
            <label>6. 疼痛程度</label>
            <div class="slider-card">
              <input v-model.number="form.painLevel" class="slider-card__input" type="range" min="0" max="4" step="1" />
              <div class="slider-card__labels">
                <span v-for="item in SYMPTOM_LEVELS" :key="item">{{ item }}</span>
              </div>
              <strong>{{ levelLabel(form.painLevel) }}</strong>
            </div>
          </div>
        </div>

        <div class="field">
          <label>7. 发生部位</label>
          <div class="choice-wrap">
            <button
              v-for="item in bodyParts"
              :key="item"
              type="button"
              class="choice-chip"
              :class="{ 'is-active': form.selectedParts.includes(item) }"
              @click="togglePart(item)"
            >
              {{ item }}
            </button>
          </div>
        </div>

        <div class="field">
          <label>8. 是否使用过药物或护肤品</label>
          <div class="choice-group">
            <button
              v-for="item in medicationOptions"
              :key="item"
              type="button"
              :class="{ 'is-active': form.medication === item }"
              @click="form.medication = item"
            >
              {{ item }}
            </button>
          </div>
        </div>

        <p v-if="feedback" class="consult-feedback">{{ feedback }}</p>

        <button type="button" class="primary-button consult-submit" :disabled="submitting" @click="submitConsultation">
          {{ submitting ? '提交中...' : '提交问诊' }}
        </button>
        <p class="consult-note">所有信息将严格保密，仅用于医生诊断与建议。</p>
      </article>

      <aside class="consult-side">
        <article class="surface-card">
          <h2 class="card-title">提交说明</h2>
          <ul class="info-list">
            <li>提交后，系统将为您智能分析图片并生成初步结果。</li>
            <li>医生会在 24 小时内查看并给出专业回复，请耐心等待。</li>
            <li>您可在历史记录中查看问诊进度与医生回复。</li>
            <li>如需进一步诊疗，医生会建议您线下就诊或复诊。</li>
          </ul>
        </article>

        <article class="surface-card">
          <h2 class="card-title">拍摄建议</h2>
          <ul class="info-list">
            <li>保证光线充足，避免逆光或阴影。</li>
            <li>拍摄清晰，确保患处对焦，可近距离拍摄。</li>
            <li>尽量拍摄患处全景与特写，帮助医生全面判断。</li>
          </ul>
        </article>

        <article class="surface-card">
          <h2 class="card-title">温馨提示</h2>
          <p class="card-copy">如症状持续加重、伴随发热等全身不适，请及时线下就医。</p>
        </article>
      </aside>
    </div>

    <div class="consult-mobile-bar">
      <button type="button" class="primary-button consult-mobile-bar__button" :disabled="submitting" @click="submitConsultation">
        {{ submitting ? '提交中...' : '提交问诊' }}
      </button>
    </div>

  </section>
</template>

<style scoped>
.consultation-page {
  padding-bottom: 88px;
}

.consult-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(300px, 0.75fr);
  gap: 18px;
}

.consult-form,
.consult-side {
  display: grid;
  gap: 18px;
}

.consult-file-input {
  display: none;
}

.upload-panel {
  display: grid;
  place-items: center;
  min-height: 180px;
  padding: 20px;
  border: 1px dashed var(--border-strong);
  border-radius: 20px;
  background:
    radial-gradient(circle at 50% 0%, rgba(224, 236, 255, 0.84), transparent 44%),
    rgba(246, 250, 255, 0.98);
  text-align: center;
  cursor: pointer;
}

.upload-panel.is-drag-over {
  border-color: rgba(47, 125, 255, 0.68);
  background: rgba(240, 247, 255, 0.98);
}

.upload-panel strong {
  color: var(--text-strong);
  font-size: 18px;
}

.upload-panel span {
  display: block;
  margin-top: 10px;
  color: var(--text-sub);
  font-size: 14px;
}

.upload-preview {
  display: grid;
  gap: 14px;
}

.upload-preview__main {
  min-height: 280px;
  padding: 14px;
  border-radius: 18px;
  border: 1px solid var(--border);
  background: rgba(246, 249, 255, 0.98);
}

.upload-preview__main img {
  width: 100%;
  height: 100%;
  max-height: 420px;
  object-fit: contain;
  border-radius: 14px;
  background: #ffffff;
}

.upload-preview__list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(108px, 1fr));
  gap: 12px;
}

.upload-preview__item {
  display: grid;
  gap: 8px;
}

.upload-preview__thumb {
  width: 100%;
  height: 108px;
  padding: 8px;
  border: 1px solid var(--border);
  border-radius: 16px;
  background: rgba(248, 250, 255, 0.98);
}

.upload-preview__thumb.is-active {
  border-color: rgba(47, 125, 255, 0.58);
  box-shadow: var(--shadow-sm);
}

.upload-preview__thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 12px;
}

.upload-preview__remove {
  justify-self: flex-start;
}

.upload-preview__more {
  min-height: 108px;
  border: 1px dashed var(--border-strong);
  border-radius: 16px;
  background: rgba(246, 250, 255, 0.98);
  color: var(--blue);
  font-weight: 700;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.choice-group,
.choice-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.choice-group button,
.choice-chip {
  min-height: 44px;
  padding: 0 16px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.96);
  color: var(--text-sub);
  font-weight: 700;
}

.choice-group button.is-active,
.choice-chip.is-active {
  border-color: rgba(47, 125, 255, 0.48);
  background: rgba(47, 125, 255, 0.1);
  color: var(--blue);
}

.slider-card {
  padding: 16px;
  border: 1px solid var(--border);
  border-radius: 18px;
  background: rgba(248, 250, 255, 0.98);
}

.slider-card__input {
  width: 100%;
}

.slider-card__labels {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
  margin-top: 10px;
  color: var(--text-faint);
  font-size: 12px;
  text-align: center;
}

.slider-card strong {
  display: block;
  margin-top: 12px;
  color: var(--text-strong);
  font-size: 15px;
}

.textarea-counter {
  text-align: right;
}

.consult-feedback {
  margin: 0;
  color: var(--rose);
  font-size: 13px;
}

.consult-submit {
  width: 100%;
}

.consult-note {
  margin: 0;
  color: var(--text-faint);
  font-size: 13px;
  text-align: center;
}

.info-list {
  margin: 14px 0 0;
  padding-left: 18px;
  color: var(--text-sub);
  font-size: 14px;
  line-height: 1.8;
}

.info-list li + li {
  margin-top: 8px;
}

.consult-mobile-bar {
  position: fixed;
  left: 12px;
  right: 12px;
  bottom: 12px;
  z-index: 30;
  display: none;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: var(--shadow-md);
}

.consult-mobile-bar__button {
  width: 100%;
}

@media (max-width: 980px) {
  .consult-layout,
  .field-grid {
    grid-template-columns: 1fr;
  }

  .consult-mobile-bar {
    display: block;
  }
}
</style>
