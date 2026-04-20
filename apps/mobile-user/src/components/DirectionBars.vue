<script setup lang="ts">
defineProps<{
  items: Array<{ label: string; value: number }>
}>()
</script>

<template>
  <div class="direction-bars">
    <div v-for="item in items" :key="item.label" class="direction-bars__item">
      <span>{{ item.label }}</span>
      <div class="direction-bars__track"><span :style="{ width: `${item.value}%` }" /></div>
      <strong>{{ item.value }}%</strong>
    </div>
  </div>
</template>
