<template>
  <div
    v-show="visible"
    class="chart-tooltip"
    :style="{ transform: `translate(${left}px, ${top}px)` }"
  >
    <span class="tooltip-time">{{ time }}</span>
    <span class="tooltip-value">{{ value }}</span>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  visible: boolean
  left: number
  top: number
  time: string
  value: string
}>()
</script>

<style scoped lang="scss">
.chart-tooltip {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 5;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 100px;
  padding: 6px 10px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  pointer-events: none;
  transition: transform 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
  will-change: transform;
}

.tooltip-time {
  color: #6b7280;
  font-size: 11px;
  font-weight: 400;
  line-height: 1.2;
}

.tooltip-value {
  color: #111827;
  font-size: 13px;
  font-weight: 600;
}
</style>
