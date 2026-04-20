<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  label: string
  tone?: 'blue' | 'violet' | 'mint' | 'amber' | 'rose' | 'slate'
}>()

const badgeTone = computed(() => props.tone || 'slate')
</script>

<template>
  <span class="status-badge" :data-tone="badgeTone">{{ label }}</span>
</template>
