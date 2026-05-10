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

    <div
      v-show="tooltip.visible"
      class="chart-marker"
      :style="{ transform: `translate(${marker.left}px, ${marker.top}px)` }"
    ></div>

    <div
      v-show="tooltip.visible"
      class="chart-tooltip"
      :style="{ transform: `translate(${tooltip.left}px, ${tooltip.top}px)` }"
    >
      <span class="tooltip-time">{{ tooltip.time }}</span>
      <span class="tooltip-value">{{ tooltip.value }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import uPlot from 'uplot'
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
const chart = ref<uPlot | null>(null)
const anchoredTimestamp = ref<number | null>(null)
const tooltip = reactive({
  visible: false,
  left: 0,
  top: 0,
  time: '',
  value: '',
})
const marker = reactive({
  left: 0,
  top: 0,
})

let resizeObserver: ResizeObserver | null = null

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

// 修改 updateTooltip 函数，支持传入鼠标原生坐标
function updateTooltip(index: number | null, mouseX?: number, mouseY?: number) {
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

  // Marker 依然锁定在数据点上（吸附效果）
  const { left: markerLeft, top: markerTop } = getPointPosition(u, timestamp, speed)
  marker.left = markerLeft
  marker.top = markerTop

  // Tooltip 使用鼠标坐标进行跟随（mouseX, mouseY 是相对于 wrapper 的）
  const tooltipWidth = 120
  const offsetX = 15
  const offsetY = 20

  // 如果没有传入鼠标坐标（比如数据更新时），回退到 marker 坐标
  const baseLeft = mouseX ?? markerLeft
  const baseTop = mouseY ?? markerTop

  // 边界计算：防止超出容器
  const nextLeft = Math.min(Math.max(baseLeft + offsetX, 8), host.clientWidth - tooltipWidth - 8)
  const nextTop = Math.min(Math.max(baseTop - offsetY - 40, 8), props.height - 50)

  tooltip.left = nextLeft
  tooltip.top = nextTop
  tooltip.time = formatTimestamp(timestamp)
  tooltip.value = formatSpeed(speed)
  tooltip.visible = true
}

// 在模板中绑定 mousemove
const handleMouseMove = (e: MouseEvent) => {
  const u = chart.value
  const host = wrapperRef.value
  if (!u || !host) return

  // 获取鼠标相对于 Canvas 绘图区的坐标
  const rect = host.getBoundingClientRect()
  const mouseX = e.clientX - rect.left
  const mouseY = e.clientY - rect.top

  // 找到最近的数据点索引
  const index = u.posToIdx(mouseX - u.bbox.left / uPlot.pxRatio)
  
  if (index != null) {
    updateTooltip(index, mouseX, mouseY)
  }
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
  updateTooltip(index)
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
    padding: [8, 8, 8, 8],
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
        values: (u: uPlot, vals: number[]) => vals.map(() => ''), // 强制清空 Y 轴刻度文字，防止漏出
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
        width: 2.5,
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
          gradient.addColorStop(0, colorMix(lineColor, 0.24))
          gradient.addColorStop(1, colorMix(lineColor, 0.02))
          return gradient
        },
      },
    ],
    hooks: {
      setCursor: [
        (u) => {
          const index = u.cursor.idx
          if (index == null) {
            tooltip.visible = false
            return
          }

          anchoredTimestamp.value = u.data[0]?.[index] ?? null
          // updateTooltip(index)
        },
      ],
    },
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
}

watch(
  () => props.data,
  (points) => {
    if (!chart.value) return

    chart.value.setData(toUplotData(points))
    nextTick(() => {
      refreshTooltip()
    })
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
  })
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
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
  transition: transform 0.2s ease-out;
  translate: -50% -50%;
}

.chart-tooltip {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 5;
  display: flex;
  flex-direction: column;
  gap: 2px;             /* 缩小行间距 */
  min-width: 100px;     /* 减小最小宽度 */
  padding: 6px 10px;    /* 更加紧凑的内边距 */
  
  /* 现代感背景：毛玻璃效果 */
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px); 
  
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 6px;   /* 减小圆角，显得干练 */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); /* 更柔和的阴影 */
  
  pointer-events: none;
  transition: transform 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
  will-change: transform; /* 告诉浏览器这是一个高频变动属性 */
}

.tooltip-time {
  color: #6b7280;       /* 更加柔和的灰色 */
  font-size: 11px;      /* 缩小字体 */
  font-weight: 400;
  line-height: 1.2;
}

.tooltip-value {
  color: #111827;
  font-size: 13px;      /* 缩小字体 */
  font-weight: 600;     /* 保持加粗以突出数据 */
}
</style>
