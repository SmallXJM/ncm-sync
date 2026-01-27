<template>
  <router-view v-slot="{ Component, route }">
    <component :is="AppLayout" v-if="route.meta.layout !== false">
      <component :is="Component" />
    </component>
    <component :is="Component" v-else />
  </router-view>
</template>

<script setup lang="ts">
import AppLayout from '@/layout/AppLayout.vue'
import { onMounted, onUnmounted } from 'vue'
import { useTheme } from '@/composables/useTheme'

const { initTheme } = useTheme()

let cleanupTheme: (() => void) | undefined

onMounted(() => {
  cleanupTheme = initTheme()
})

onUnmounted(() => {
  if (cleanupTheme) cleanupTheme()
})
</script>
