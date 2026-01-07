<template>
  <router-view v-slot="{ Component, route }">
    <component :is="route.meta.layout === false ? Component : AppLayout">
      <component :is="Component" />
    </component>
  </router-view>
</template>

<script setup lang="ts">
import AppLayout from '@/layout/AppLayout.vue'
</script>
