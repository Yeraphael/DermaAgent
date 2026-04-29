<script setup lang="ts">
defineProps<{
  compact?: boolean
}>()
</script>

<template>
  <div class="brand-mark" :class="{ compact }">
    <div class="brand-mark__icon" aria-hidden="true">
      <span class="node node-a" />
      <span class="node node-b" />
      <span class="node node-c" />
      <span class="node node-d" />
      <span class="node node-e" />
      <span class="link link-a" />
      <span class="link link-b" />
      <span class="link link-c" />
    </div>
    <div class="brand-mark__copy">
      <strong>肤联智诊</strong>
      <span>智能问诊 · 智护肌肤</span>
    </div>
  </div>
</template>
