<template>
  <div
    ref="tooltipRef"
    v-show="visible"
    class="chart-tooltip"
    :style="{ transform: `translate(${left}px, ${top}px)` }"
  >
    <span class="tooltip-time">{{ time }}</span>
    <span v-for="item in items" :key="item.title" class="tooltip-row">
      <span class="tooltip-indicator" :style="{ background: item.color }"></span>
      <span class="tooltip-title">{{ item.title }}</span>
      <span class="tooltip-value">{{ item.value }}</span>
    </span>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface TooltipItem {
  title: string
  value: string
  color: string
}

defineProps<{
  visible: boolean
  left: number
  top: number
  time: string
  items: TooltipItem[]
}>()

const tooltipRef = ref<HTMLElement | null>(null)

defineExpose({
  tooltipRef,
})
</script>

<style scoped lang="scss">
.chart-tooltip {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 5;
  display: flex;
  flex-direction: column;
  min-width: 140px;
  padding: 0 var(--spacing-sm);

  background: color-mix(in srgb, var(--bg-body) 68%, transparent);
  backdrop-filter: blur(6px);
  border: 1px solid color-mix(in srgb, var(--border-color) 72%, transparent);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  
  pointer-events: none;
  transition: transform 0.5s cubic-bezier(0.2, 0.8, 0.2, 1);
  will-change: transform;
}

.tooltip-time {
  color: var(--text-primary);
  font-size: 0.72rem;
  font-weight: 400;
  font-variant-numeric: tabular-nums;
}

.tooltip-row {
  display: flex;
  align-items: center;
  // justify-content: space-between;
  gap: var(--spacing-sm);
}

.tooltip-indicator {
  flex: 0 0 auto;
  width: 4px;
  height: 0.72rem;
  border-radius: var(--radius-full);
}

.tooltip-title {
  color: var(--text-secondary);
  font-size: 0.72rem;
  font-weight: 400;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.tooltip-value {
  margin-left: auto;
  color: var(--text-primary);
  font-size: 0.72rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
</style>
