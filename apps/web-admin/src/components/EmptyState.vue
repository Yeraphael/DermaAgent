<script setup lang="ts">
defineProps<{
  title: string
  copy: string
}>()
</script>

<template>
  <div class="empty-state">
    <div class="empty-state__orb" />
    <strong>{{ title }}</strong>
    <p>{{ copy }}</p>
  </div>
</template>
