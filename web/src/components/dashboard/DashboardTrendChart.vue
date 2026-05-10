<template>
  <div
    ref="wrapperRef"
    class="trend-chart"
    :style="{ height: `${height}px` }"
    @mousemove="handleMouseMove"
    @mouseleave="hideTooltip"
  >
    <div ref="chartRef" class="trend-chart-canvas"></div>

    <div v-if="!hasData" class="chart-empty">{{ emptyText }}</div>

    <DashboardChartMarker :visible="tooltip.visible" :left="marker.left" :top="marker.top" />

    <DashboardChartTooltip
      ref="tooltipComponentRef"
      :visible="tooltip.visible"
      :left="tooltip.left"
      :top="tooltip.top"
      :time="tooltip.time"
      :value="tooltip.value"
      :title="tooltip.title"
      :color="color"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import uPlot from 'uplot'
import DashboardChartMarker from './DashboardChartMarker.vue'
import DashboardChartTooltip from './DashboardChartTooltip.vue'
import 'uplot/dist/uPlot.min.css'

interface TrendPoint {
  x: number
  y: number
}

const props = withDefaults(
  defineProps<{
    data: TrendPoint[]
    height?: number
    color?: string
    unit?: string
    emptyText?: string
  }>(),
  {
    height: 220,
    color: '#111827',
    unit: 'B/s',
    emptyText: '暂无数据',
  },
)

const wrapperRef = ref<HTMLElement | null>(null)
const chartRef = ref<HTMLElement | null>(null)
const tooltipComponentRef = ref<InstanceType<typeof DashboardChartTooltip> | null>(null)
const chart = ref<uPlot | null>(null)
const anchoredTimestamp = ref<number | null>(null)
const tooltip = reactive({
  visible: false,
  left: 0,
  top: 0,
  time: '',
  value: '',
  title: '',
})
const marker = reactive({
  left: 0,
  top: 0,
})

let resizeObserver: ResizeObserver | null = null
let themeObserver: MutationObserver | null = null
let colorSchemeMq: MediaQueryList | null = null

const hasData = computed(() => props.data.length > 0)

function resolveCssColor(value: string): string {
  const host = wrapperRef.value
  if (!host || !value.startsWith('var(')) return value

  const name = value.slice(4, -1).trim()
  return getComputedStyle(host).getPropertyValue(name).trim() || value
}

function toUplotData(points: TrendPoint[]): uPlot.AlignedData {
  return [points.map((point) => point.x / 1000), points.map((point) => point.y)]
}

function formatSpeed(bytesPerSecond: number): string {
  if (!Number.isFinite(bytesPerSecond) || bytesPerSecond <= 0) return `0 ${props.unit}`

  const units = ['B/s', 'KB/s', 'MB/s', 'GB/s']
  const base = 1024
  const index = Math.min(Math.floor(Math.log(bytesPerSecond) / Math.log(base)), units.length - 1)
  const value = bytesPerSecond / Math.pow(base, index)
  return `${value.toFixed(index === 0 ? 0 : 2)} ${units[index]}`
}

function formatTimestamp(seconds: number): string {
  if (!Number.isFinite(seconds)) return '--'
  return new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(new Date(seconds * 1000))
}

function findIndexByTimestamp(u: uPlot, timestamp: number): number | null {
  const timestamps = u.data[0] ?? []
  if (timestamps.length === 0) return null

  let closestIndex: number | null = null
  let closestDistance = Number.POSITIVE_INFINITY

  for (let index = 0; index < timestamps.length; index += 1) {
    const item = timestamps[index]
    if (item == null) continue

    const distance = Math.abs(item - timestamp)
    if (distance < closestDistance) {
      closestDistance = distance
      closestIndex = index
    }
  }

  return closestIndex
}

function getPointPosition(u: uPlot, timestamp: number, value: number) {
  const plotLeft = u.bbox.left / uPlot.pxRatio
  const plotTop = u.bbox.top / uPlot.pxRatio

  return {
    left: plotLeft + u.valToPos(timestamp, 'x'),
    top: plotTop + u.valToPos(value, 'y'),
  }
}

function getTooltipSize() {
  const element = tooltipComponentRef.value?.tooltipRef

  return {
    width: element?.offsetWidth || 120,
    height: element?.offsetHeight || 48,
  }
}

function updateTooltip(
  index: number | null,
  mouseX?: number,
  mouseY?: number,
  shouldUpdateTooltipPosition = true,
) {
  const u = chart.value
  const host = wrapperRef.value
  if (!u || !host || index == null) {
    tooltip.visible = false
    return
  }

  const timestamp = u.data[0]?.[index]
  const speed = u.data[1]?.[index]
  if (timestamp == null || speed == null) {
    tooltip.visible = false
    return
  }

  const { left: markerLeft, top: markerTop } = getPointPosition(u, timestamp, speed)
  const tooltipSize = getTooltipSize()
  const gap = 12
  const baseLeft = mouseX ?? markerLeft
  const baseTop = mouseY ?? markerTop

  marker.left = markerLeft
  marker.top = markerTop
  if (shouldUpdateTooltipPosition) {
    const rightLeft = baseLeft + gap
    const leftLeft = baseLeft - tooltipSize.width - gap
    const upperTop = baseTop - tooltipSize.height - gap
    const lowerTop = baseTop + gap
    const nextLeft = rightLeft + tooltipSize.width <= host.clientWidth - 8 ? rightLeft : leftLeft
    const nextTop = upperTop >= 8 ? upperTop : lowerTop

    tooltip.left = Math.min(Math.max(nextLeft, 8), host.clientWidth - tooltipSize.width - 8)
    tooltip.top = Math.min(Math.max(nextTop, 8), props.height - tooltipSize.height - 8)
  }

  tooltip.title = '下载速度'
  tooltip.time = formatTimestamp(timestamp)
  tooltip.value = formatSpeed(speed)
  tooltip.visible = true
}

function handleMouseMove(event: MouseEvent) {
  const u = chart.value
  const host = wrapperRef.value
  if (!u || !host) return

  const rect = host.getBoundingClientRect()
  const mouseX = event.clientX - rect.left
  const mouseY = event.clientY - rect.top
  const plotLeft = u.bbox.left / uPlot.pxRatio
  const index = u.posToIdx(mouseX - plotLeft)

  if (index == null) return

  anchoredTimestamp.value = u.data[0]?.[index] ?? null
  updateTooltip(index, mouseX, mouseY)
}

function refreshTooltip() {
  const u = chart.value
  const timestamp = anchoredTimestamp.value
  if (!u || timestamp == null) return

  const index = findIndexByTimestamp(u, timestamp)
  if (index == null) {
    hideTooltip()
    return
  }

  const nextTimestamp = u.data[0]?.[index]
  const speed = u.data[1]?.[index]
  if (nextTimestamp == null || speed == null) {
    hideTooltip()
    return
  }

  anchoredTimestamp.value = nextTimestamp
  updateTooltip(index, undefined, undefined, false)
}

function hideTooltip() {
  tooltip.visible = false
  anchoredTimestamp.value = null
}

function createOptions(width: number): uPlot.Options {
  const lineColor = resolveCssColor(props.color)

  return {
    width,
    height: props.height,
    padding: [8, 0, 8, 0],
    cursor: {
      x: false,
      y: false,
      drag: { x: false, y: false },
      points: { show: false },
    },
    legend: {
      show: false,
    },
    scales: {
      x: { time: true },
      y: { auto: true, range: (_u, min, max) => [0, Math.max(max, min + 1)] },
    },
    axes: [
      {
        show: false,
        scale: 'x',
      },
      {
        show: true,
        scale: 'y',
        size: 0,
        ticks: { show: false },
        border: { show: false },
        values: (_u, values) => values.map(() => ''),
        grid: {
          show: true,
          stroke: 'rgba(148, 163, 184, 0.18)',
          dash: [4, 4],
          width: 1,
        },
      },
    ],
    series: [
      {},
      {
        label: '下载速度',
        stroke: lineColor,
        width: 2,
        paths: uPlot.paths.spline?.(),
        points: {
          show: false,
          size: 5,
          width: 1.5,
          stroke: lineColor,
          fill: resolveCssColor('var(--bg-surface)'),
        },
        fill: (u, seriesIndex) => {
          if (seriesIndex !== 1) return 'rgba(17, 24, 39, 0.08)'

          const gradient = u.ctx.createLinearGradient(0, 0, 0, props.height)
          gradient.addColorStop(1, colorMix(lineColor, 0.2))
          return gradient
        },
      },
    ],
  }
}

function colorMix(color: string, alpha: number): string {
  if (color.startsWith('#')) {
    const hex = color.slice(1)
    const normalized =
      hex.length === 3
        ? hex
            .split('')
            .map((item) => item + item)
            .join('')
        : hex

    const value = Number.parseInt(normalized, 16)
    const red = (value >> 16) & 255
    const green = (value >> 8) & 255
    const blue = value & 255
    return `rgba(${red}, ${green}, ${blue}, ${alpha})`
  }

  return `color-mix(in srgb, ${color} ${Math.round(alpha * 100)}%, transparent)`
}

function mountChart() {
  const host = chartRef.value
  const wrapper = wrapperRef.value
  if (!host || !wrapper) return

  chart.value?.destroy()
  chart.value = new uPlot(createOptions(wrapper.clientWidth), toUplotData(props.data), host)
  refreshTooltip()
}

function handleThemeChange() {
  nextTick(mountChart)
}

watch(
  () => props.data,
  (points) => {
    if (!chart.value) return

    chart.value.setData(toUplotData(points))
    nextTick(refreshTooltip)
  },
  { deep: true },
)

watch(
  () => [props.height, props.color],
  () => {
    nextTick(mountChart)
  },
)

onMounted(() => {
  nextTick(() => {
    mountChart()

    if (!wrapperRef.value) return
    resizeObserver = new ResizeObserver(([entry]) => {
      if (!entry) return

      const width = Math.floor(entry.contentRect.width)
      if (width <= 0) return

      chart.value?.setSize({ width, height: props.height })
      refreshTooltip()
    })
    resizeObserver.observe(wrapperRef.value)

    themeObserver = new MutationObserver(handleThemeChange)
    themeObserver.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class'],
    })

    colorSchemeMq = window.matchMedia('(prefers-color-scheme: dark)')
    colorSchemeMq.addEventListener('change', handleThemeChange)
  })
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  themeObserver?.disconnect()
  colorSchemeMq?.removeEventListener('change', handleThemeChange)
  chart.value?.destroy()
})
</script>

<style scoped lang="scss">
.trend-chart {
  position: relative;
  width: 100%;
  min-height: 160px;
}

.trend-chart-canvas {
  width: 100%;
  height: 100%;

  :deep(.uplot) {
    width: 100%;
    font-family: ui-sans-serif, system-ui, sans-serif;
  }

  :deep(.u-over) {
    cursor: default;
  }
}

.chart-empty {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  color: var(--text-tertiary);
  font-size: 0.85rem;
  pointer-events: none;
}
</style>
