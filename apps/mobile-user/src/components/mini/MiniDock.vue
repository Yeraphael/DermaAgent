<script setup lang="ts">
import { openMiniTab, type MiniTabKey } from '../../utils/miniPortal'

defineProps<{
  active: MiniTabKey
}>()

const items: Array<{ key: MiniTabKey; label: string }> = [
  { key: 'home', label: '首页' },
  { key: 'consultation', label: '问诊' },
  { key: 'qa', label: '问答' },
  { key: 'history', label: '消息' },
  { key: 'profile', label: '我的' },
]
</script>

<template>
  <view class="mini-dock">
    <view
      v-for="item in items"
      :key="item.key"
      class="mini-dock__item"
      :class="{ 'is-active': active === item.key }"
      @click="openMiniTab(item.key)"
    >
      {{ item.label }}
    </view>
  </view>
</template>
