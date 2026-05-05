<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import PanelCard from '@/components/PanelCard.vue'
import { fetchAdminConfigs, updateAdminConfig, type ConfigItem } from '@/api/workspace'
import { cleanVisibleText, parseConfigValue, stringifyConfigValue } from '@/utils/workspace'

const loading = ref(false)
const savingKey = ref('')
const configGroups = ref<Record<string, ConfigItem[]>>({})
const drafts = reactive<Record<string, unknown>>({})

const groupMeta: Record<string, { title: string; subtitle: string }> = {
  AI_MODEL: {
    title: '模型参数配置',
    subtitle: '维护图文分析模型、温度、超时时间与最大输出长度。',
  },
  PROMPT: {
    title: '提示词模板管理',
    subtitle: '统一维护图文问诊与知识问答提示词模板。',
  },
  RISK: {
    title: '风险等级规则',
    subtitle: '配置低、中、高风险分级阈值与建议动作。',
  },
  UPLOAD: {
    title: '图片上传限制',
    subtitle: '维护上传数量、大小限制和文件格式规则。',
  },
  NOTICE: {
    title: '通知规则',
    subtitle: '控制医生回复、高风险和分析完成通知策略。',
  },
  PERMISSION: {
    title: '角色与权限',
    subtitle: '查看不同角色的权限矩阵与平台访问边界。',
  },
}

const orderedGroups = computed(() => {
  const preferred = ['AI_MODEL', 'PROMPT', 'RISK', 'UPLOAD', 'NOTICE', 'PERMISSION']
  return preferred.filter((key) => configGroups.value[key]?.length)
})

function normalizeDraft(item: ConfigItem) {
  if (item.config_key === 'ai.mode') {
    return item.config_value === 'real' ? 'real' : 'standard'
  }
  if (item.config_key === 'ai.visual_model') {
    return item.config_value.includes('mock') ? 'Qwen2.5-VL' : item.config_value
  }
  return parseConfigValue(item.config_value, item.value_type)
}

function syncDrafts(groups: Record<string, ConfigItem[]>) {
  Object.values(groups)
    .flat()
    .forEach((item) => {
      drafts[item.config_key] = normalizeDraft(item)
    })
}

async function loadConfigs() {
  try {
    loading.value = true
    const result = await fetchAdminConfigs()
    configGroups.value = result.groups
    syncDrafts(result.groups)
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    loading.value = false
  }
}

function displayValue(item: ConfigItem) {
  const draft = drafts[item.config_key]
  if (item.value_type === 'json') {
    return stringifyConfigValue(draft)
  }
  return typeof draft === 'string' ? cleanVisibleText(draft, '') : draft
}

function updateDraftText(configKey: string, value: string) {
  drafts[configKey] = value
}

async function saveItem(item: ConfigItem) {
  try {
    savingKey.value = item.config_key
    let payload: unknown = drafts[item.config_key]
    if (item.value_type === 'number') {
      payload = Number(payload)
    }
    if (item.value_type === 'json' && typeof payload === 'string') {
      payload = JSON.parse(payload)
    }
    await updateAdminConfig(item.config_key, payload)
    ElMessage.success('配置已保存。')
    await loadConfigs()
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    savingKey.value = ''
  }
}

onMounted(loadConfigs)
</script>

<template>
  <div class="page-shell" v-loading="loading">
    <section v-for="groupKey in orderedGroups" :key="groupKey">
      <PanelCard :title="groupMeta[groupKey].title" :subtitle="groupMeta[groupKey].subtitle">
        <div class="settings-grid">
          <article
            v-for="item in configGroups[groupKey]"
            :key="item.config_key"
            class="surface-card surface-card--compact settings-card"
          >
            <div class="tiny-label">{{ item.config_key }}</div>
            <h3 class="panel-title settings-card__title">{{ cleanVisibleText(item.description || item.config_key) }}</h3>

            <div class="form-field" style="margin-top: 18px;">
              <template v-if="item.config_key === 'ai.mode'">
                <label>运行模式</label>
                <div class="segment">
                  <button
                    type="button"
                    class="segment-button"
                    :class="{ 'is-active': drafts[item.config_key] === 'standard' }"
                    @click="drafts[item.config_key] = 'standard'"
                  >
                    标准模式
                  </button>
                  <button
                    type="button"
                    class="segment-button"
                    :class="{ 'is-active': drafts[item.config_key] === 'real' }"
                    @click="drafts[item.config_key] = 'real'"
                  >
                    实时模型
                  </button>
                </div>
              </template>

              <template v-else-if="item.value_type === 'boolean'">
                <label>{{ cleanVisibleText(item.description || item.config_key) }}</label>
                <div class="segment">
                  <button
                    type="button"
                    class="segment-button"
                    :class="{ 'is-active': drafts[item.config_key] === true }"
                    @click="drafts[item.config_key] = true"
                  >
                    开启
                  </button>
                  <button
                    type="button"
                    class="segment-button"
                    :class="{ 'is-active': drafts[item.config_key] === false }"
                    @click="drafts[item.config_key] = false"
                  >
                    关闭
                  </button>
                </div>
              </template>

              <template v-else-if="item.value_type === 'textarea' || item.value_type === 'json'">
                <label>{{ cleanVisibleText(item.description || item.config_key) }}</label>
                <textarea
                  class="ghost-textarea"
                  :value="String(displayValue(item) || '')"
                  @input="updateDraftText(item.config_key, ($event.target as HTMLTextAreaElement).value)"
                />
              </template>

              <template v-else-if="item.value_type === 'number'">
                <label>{{ cleanVisibleText(item.description || item.config_key) }}</label>
                <el-input-number
                  :model-value="Number(drafts[item.config_key] || 0)"
                  :controls="false"
                  style="width: 100%;"
                  @update:model-value="(value) => { drafts[item.config_key] = value ?? 0 }"
                />
              </template>

              <template v-else>
                <label>{{ cleanVisibleText(item.description || item.config_key) }}</label>
                <input
                  class="ghost-input"
                  :value="String(displayValue(item) || '')"
                  @input="updateDraftText(item.config_key, ($event.target as HTMLInputElement).value)"
                />
              </template>
            </div>

            <div class="action-row" style="margin-top: 16px;">
              <button
                type="button"
                class="primary-button"
                :disabled="savingKey === item.config_key"
                @click="saveItem(item)"
              >
                {{ savingKey === item.config_key ? '保存中…' : '保存配置' }}
              </button>
            </div>
          </article>
        </div>
      </PanelCard>
    </section>
  </div>
</template>
