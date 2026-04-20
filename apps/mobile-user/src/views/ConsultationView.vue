<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import DirectionBars from '../components/DirectionBars.vue'
import RiskBadge from '../components/RiskBadge.vue'
import { buildVisualStyle, submitPortalConsultation } from '../shared/portal'

const router = useRouter()
const loading = ref(false)
const previews = ref<string[]>([])
const form = reactive({
  description: '',
  onsetDuration: '2 天内',
  itchLevel: 3,
  painLevel: 1,
  spreadFlag: false,
  spreadParts: ['面部'] as string[],
})

const directionPreview = computed(() => [
  { label: '接触性皮炎', value: form.description.includes('痘') ? 18 : 45 },
  { label: '湿疹样反应', value: form.spreadFlag ? 32 : 25 },
  { label: '屏障受损', value: form.description.includes('干') || form.description.includes('脱皮') ? 42 : 15 },
  { label: '口周皮炎', value: form.description.includes('丘疹') ? 28 : 10 },
])

function handleFiles(event: Event) {
  const target = event.target as HTMLInputElement
  const selected = Array.from(target.files || []).slice(0, 5)
  previews.value = selected.map((file) => URL.createObjectURL(file))
}

function toggleSpreadPart(part: string) {
  if (form.spreadParts.includes(part)) {
    form.spreadParts = form.spreadParts.filter((item) => item !== part)
  } else {
    form.spreadParts = [...form.spreadParts, part]
  }
}

async function submit() {
  if (!form.description.trim()) return
  loading.value = true
  const result = await submitPortalConsultation({
    description: form.description,
    onsetDuration: form.onsetDuration,
    itchLevel: form.itchLevel,
    painLevel: form.painLevel,
    spreadFlag: form.spreadFlag,
    spreadParts: form.spreadParts,
    visuals: previews.value,
  })
  loading.value = false
  router.push(`/analysis/${result.caseId}`)
}
</script>

<template>
  <section class="analysis-layout">
    <article class="surface-card">
      <div class="section-head">
        <div>
          <p class="section-eyebrow">Step 01</p>
          <h1 class="section-title">提交症状信息</h1>
          <p class="section-subtitle">上传皮肤图片、描述症状、补充时长、瘙痒和疼痛程度，让 AI 给出初步观察。</p>
        </div>
      </div>

      <div class="page-stack">
        <div class="field">
          <label>上传皮肤图片（1-5 张）</label>
          <input class="ghost-input" type="file" accept="image/*" multiple @change="handleFiles" />
          <div class="upload-strip">
            <div v-for="item in previews.slice(0, 5)" :key="item" class="visual-tile" :style="buildVisualStyle(item)" />
            <div v-for="index in Math.max(0, 5 - previews.length)" :key="index" class="upload-tile">+</div>
          </div>
        </div>

        <div class="field">
          <label>症状描述</label>
          <textarea v-model="form.description" class="ghost-textarea" maxlength="300" placeholder="例如：两颊突然出现泛红和小疹子，伴有瘙痒，最近更换过护肤品。" />
        </div>

        <div class="grid-2">
          <div class="field">
            <label>发病时长</label>
            <select v-model="form.onsetDuration" class="ghost-select">
              <option>今天</option>
              <option>2 天内</option>
              <option>3 天内</option>
              <option>1 周内</option>
              <option>1 个月</option>
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
              <span :style="{ color: form.spreadParts.includes(item) ? '#183b82' : '#6f7ea8' }">{{ item }}</span>
            </button>
          </div>
        </div>

        <button type="button" class="primary-button" @click="submit">
          {{ loading ? '正在生成 AI 结果…' : '提交问诊' }}
        </button>
      </div>
    </article>

    <article class="surface-card">
      <div class="section-head">
        <div>
          <p class="section-eyebrow">Step 02</p>
          <h2 class="card-title">AI 分析结果（预览）</h2>
        </div>
        <RiskBadge :label="form.spreadFlag || form.painLevel >= 4 ? '中高风险' : '中低风险'" :tone="form.spreadFlag || form.painLevel >= 4 ? 'amber' : 'mint'" />
      </div>
      <p class="card-copy">
        系统会根据你的图片和症状描述生成初步观察、可能相关方向、护理建议和是否建议就医的提醒。
      </p>
      <div class="surface-card surface-card--compact" style="margin-top: 18px;">
        <p class="section-eyebrow">图片初步观察</p>
        <p class="card-copy">可见局部红斑、丘疹或干燥脱屑，结合症状信息给出分层判断。</p>
      </div>
      <div class="surface-card surface-card--compact" style="margin-top: 18px;">
        <p class="section-eyebrow">可能相关方向</p>
        <DirectionBars :items="directionPreview" />
      </div>
      <div class="surface-card surface-card--compact" style="margin-top: 18px;">
        <p class="section-eyebrow">护理建议</p>
        <div class="timeline-list" style="margin-top: 12px;">
          <article class="timeline-item">
            <strong>先修护后观察</strong>
            <p>暂停新增活性护肤，优先保湿与屏障修护。</p>
          </article>
          <article class="timeline-item">
            <strong>必要时接入医生</strong>
            <p>如存在扩散、疼痛或持续加重，会自动进入医生复核流程。</p>
          </article>
        </div>
      </div>
    </article>

    <article class="surface-card">
      <div class="section-head">
        <div>
          <p class="section-eyebrow">Step 03</p>
          <h2 class="card-title">知识问答与提醒</h2>
        </div>
      </div>
      <div class="timeline-list">
        <article class="timeline-item">
          <strong>输入你的问题，例如：泛红如何护理？</strong>
          <p>在提交问诊后，你还可以继续进入知识问答页，结合护理知识做进一步理解。</p>
        </article>
        <article class="timeline-item">
          <strong>护理建议样例</strong>
          <p>轻度泛红在避免刺激、做好保湿修护的情况下可能逐渐缓解，但若反复出现，建议及时复核。</p>
        </article>
        <article class="timeline-item">
          <strong>风险说明</strong>
          <p>本系统内容仅供辅助参考，不作为最终诊断依据。</p>
        </article>
      </div>
    </article>
  </section>
</template>
