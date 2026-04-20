<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
  change?: string
  note?: string
  accent?: 'blue' | 'violet' | 'sky' | 'mint' | 'rose' | 'lilac'
}>()
</script>

<template>
  <article class="metric-card" :data-accent="accent || 'blue'">
    <div class="metric-card__glow" />
    <div class="metric-card__head">
      <span class="metric-card__label">{{ label }}</span>
      <span v-if="change" class="metric-card__change">{{ change }}</span>
    </div>
    <strong class="metric-card__value">{{ value }}</strong>
    <p v-if="note" class="metric-card__note">{{ note }}</p>
    <slot />
  </article>
</template>
