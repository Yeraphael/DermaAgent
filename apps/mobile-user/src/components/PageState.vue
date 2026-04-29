<script setup lang="ts">
withDefaults(
  defineProps<{
    title: string
    description?: string
    actionText?: string
    tone?: 'default' | 'error' | 'empty'
  }>(),
  {
    description: '',
    actionText: '',
    tone: 'default',
  },
)

defineEmits<{
  (event: 'action'): void
}>()
</script>

<template>
  <article class="surface-card page-state" :data-tone="tone">
    <div class="page-state__dot" />
    <h2>{{ title }}</h2>
    <p v-if="description">{{ description }}</p>
    <button v-if="actionText" type="button" class="primary-button" @click="$emit('action')">
      {{ actionText }}
    </button>
  </article>
</template>
