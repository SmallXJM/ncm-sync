<template>
  <div
    v-show="visible"
    class="chart-marker"
    :style="{ transform: `translate(${left}px, ${top}px)`, background: color }"
  ></div>
</template>

<script setup lang="ts">
defineProps<{
  visible: boolean
  left: number
  top: number
  color?: string
}>()
</script>

<style scoped lang="scss">
.chart-marker {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 4;
  width: 12px;
  height: 12px;
  border: 3px solid var(--bg-surface);
  border-radius: 50%;
  background: var(--accent-color);
  box-shadow: var(--shadow-sm);
  pointer-events: none;
  transition: transform 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
  translate: -50% -50%;
}
</style>
