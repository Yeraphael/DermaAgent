<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  label: string
  tone?: 'blue' | 'violet' | 'mint' | 'amber' | 'rose' | 'slate'
}>()

const tone = computed(() => props.tone || 'blue')
</script>

<template>
  <span class="risk-badge" :data-tone="tone">{{ label }}</span>
</template>
