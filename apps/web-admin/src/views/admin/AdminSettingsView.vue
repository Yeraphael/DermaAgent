<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import PanelCard from '@/components/PanelCard.vue'
import { getAdminWorkspace, updateConfig } from '@/data/controlCenter'

const workspace = ref<Awaited<ReturnType<typeof getAdminWorkspace>> | null>(null)

async function loadWorkspace() {
  workspace.value = await getAdminWorkspace()
}

async function saveConfig(configKey: string, value: string | number | boolean) {
  await updateConfig(configKey, value)
  await loadWorkspace()
  ElMessage.success('配置已更新')
}

function saveTextConfig(configKey: string, event: Event) {
  const target = event.target as HTMLInputElement
  saveConfig(configKey, target.value)
}

onMounted(loadWorkspace)
</script>

<template>
  <PanelCard title="系统配置" subtitle="Prompt 模板版本、医生复核开关、文件上传限制等关键配置统一收束在产品化配置面板里。">
    <div class="split-grid">
      <article
        v-for="item in workspace?.configs || []"
        :key="item.config_key"
        class="surface-card surface-card--compact"
      >
        <div class="tiny-label">{{ item.config_key }}</div>
        <h3 class="panel-title" style="font-size: 22px; margin-top: 8px;">{{ item.title }}</h3>
        <p class="panel-subtitle">{{ item.description }}</p>

        <div class="form-field" style="margin-top: 18px;">
          <template v-if="item.type === 'switch'">
            <div class="segment">
              <button type="button" class="segment-button" :class="{ 'is-active': item.config_value === true }" @click="saveConfig(item.config_key, true)">开启</button>
              <button type="button" class="segment-button" :class="{ 'is-active': item.config_value === false }" @click="saveConfig(item.config_key, false)">关闭</button>
            </div>
          </template>
          <template v-else>
            <input
              class="ghost-input"
              :value="item.config_value"
              @change="saveTextConfig(item.config_key, $event)"
            />
          </template>
        </div>
      </article>
    </div>
  </PanelCard>
</template>
