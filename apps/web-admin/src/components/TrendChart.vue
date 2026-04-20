<script setup lang="ts">
import { computed } from 'vue'

type Point = {
  label: string
  consultations: number
  highRisk: number
}

const props = defineProps<{
  points: Point[]
}>()

function buildPath(values: number[], width: number, height: number) {
  if (!values.length) {
    return ''
  }

  const max = Math.max(...values, 1)
  const step = width / Math.max(values.length - 1, 1)
  return values
    .map((value, index) => {
      const x = index * step
      const y = height - (value / max) * height
      return `${index === 0 ? 'M' : 'L'}${x},${y}`
    })
    .join(' ')
}

const width = 460
const height = 190

const primaryValues = computed(() => props.points.map((item) => item.consultations))
const secondaryValues = computed(() => props.points.map((item) => item.highRisk))

const primaryPath = computed(() => buildPath(primaryValues.value, width, height))
const secondaryPath = computed(() => buildPath(secondaryValues.value, width, height))
const areaPath = computed(() => {
  if (!primaryPath.value) return ''
  return `${primaryPath.value} L ${width},${height} L 0,${height} Z`
})
</script>

<template>
  <div class="trend-chart">
    <svg :viewBox="`0 0 ${width} ${height}`" preserveAspectRatio="none" class="trend-chart__svg">
      <defs>
        <linearGradient id="trend-fill" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="rgba(74, 132, 255, 0.28)" />
          <stop offset="100%" stop-color="rgba(74, 132, 255, 0)" />
        </linearGradient>
      </defs>
      <path v-if="areaPath" :d="areaPath" fill="url(#trend-fill)" />
      <path v-if="primaryPath" :d="primaryPath" class="trend-chart__line trend-chart__line--primary" />
      <path v-if="secondaryPath" :d="secondaryPath" class="trend-chart__line trend-chart__line--secondary" />
    </svg>
    <div class="trend-chart__labels">
      <span v-for="item in points" :key="item.label">{{ item.label }}</span>
    </div>
  </div>
</template>
