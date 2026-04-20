<script setup lang="ts">
defineProps<{
  title?: string
  subtitle?: string
  eyebrow?: string
  compact?: boolean
}>()
</script>

<template>
  <section class="surface-card" :class="{ 'surface-card--compact': compact }">
    <header v-if="title || subtitle || eyebrow || $slots.actions" class="panel-head">
      <div>
        <div v-if="eyebrow" class="panel-eyebrow">{{ eyebrow }}</div>
        <h3 v-if="title" class="panel-title">{{ title }}</h3>
        <p v-if="subtitle" class="panel-subtitle">{{ subtitle }}</p>
      </div>
      <div v-if="$slots.actions" class="panel-actions">
        <slot name="actions" />
      </div>
    </header>
    <slot />
  </section>
</template>
