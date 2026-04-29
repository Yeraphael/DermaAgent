<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    visible: boolean
    title: string
    description?: string
    confirmText?: string
    cancelText?: string
    danger?: boolean
    loading?: boolean
  }>(),
  {
    description: '',
    confirmText: '确认',
    cancelText: '取消',
    danger: false,
    loading: false,
  },
)

const emit = defineEmits<{
  (event: 'cancel'): void
  (event: 'confirm'): void
}>()

function handleBackdropClick(event: MouseEvent) {
  if (event.target === event.currentTarget && !props.loading) {
    emit('cancel')
  }
}
</script>

<template>
  <teleport to="body">
    <div v-if="visible" class="dialog-backdrop" @click="handleBackdropClick">
      <div class="dialog-panel">
        <div class="dialog-panel__header">
          <h3>{{ title }}</h3>
          <p v-if="description">{{ description }}</p>
        </div>

        <div class="dialog-panel__actions">
          <button type="button" class="secondary-button" :disabled="loading" @click="emit('cancel')">
            {{ cancelText }}
          </button>
          <button
            type="button"
            class="primary-button"
            :class="{ 'primary-button--danger': danger }"
            :disabled="loading"
            @click="emit('confirm')"
          >
            {{ loading ? '处理中...' : confirmText }}
          </button>
        </div>
      </div>
    </div>
  </teleport>
</template>
