<template>
  <div
    ref="wrapperRef"
    class="bar-chart"
    :style="{ height: `${height}px` }"
    @mousemove="handleMouseMove"
    @mouseleave="hideTooltip"
  >
    <div ref="chartRef" class="bar-chart-canvas"></div>

    <div v-if="!hasData" class="chart-empty">{{ emptyText }}</div>

    <ChartTooltip
      ref="tooltipComponentRef"
      :visible="tooltip.visible"
      :left="tooltip.left"
      :top="tooltip.top"
      :time="tooltip.time"
      :items="tooltip.items"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import uPlot from 'uplot'
import ChartTooltip from './ChartTooltip.vue'
import {
  colorMix,
  resolveCssColor,
  type BarChartSeries,
  type ChartTooltipItem,
} from './chartUtils'
import 'uplot/dist/uPlot.min.css'

const props = withDefaults(
  defineProps<{
    series: BarChartSeries[]
    height?: number
    emptyText?: string
    valueFormatter?: (value: number, series: BarChartSeries) => string
    xFormatter?: (value: string) => string
  }>(),
  {
    height: 220,
    emptyText: '暂无数据',
    valueFormatter: (value: number) => String(value),
    xFormatter: (value: string) => value,
  },
)

const wrapperRef = ref<HTMLElement | null>(null)
const chartRef = ref<HTMLElement | null>(null)
const tooltipComponentRef = ref<InstanceType<typeof ChartTooltip> | null>(null)
const chart = ref<uPlot | null>(null)
const tooltip = reactive({
  visible: false,
  left: 0,
  top: 0,
  time: '',
  items: [] as ChartTooltipItem[],
})

let resizeObserver: ResizeObserver | null = null
let themeObserver: MutationObserver | null = null
let colorSchemeMq: MediaQueryList | null = null

const hasData = computed(() => props.series.some((item) => item.data.length > 0))

function getPrimarySeries(): BarChartSeries | null {
  return props.series[0] ?? null
}

function getResolvedColor(color: string): string {
  return resolveCssColor(color, wrapperRef.value)
}

function getXAxis(): number[] {
  const primary = getPrimarySeries()
  return primary?.data.map((_, index) => index) ?? []
}

function toUplotData(): uPlot.AlignedData {
  return [
    getXAxis(),
    ...props.series.map((item) => item.data.map((point) => point.y)),
  ]
}

function getTooltipSize() {
  const element = tooltipComponentRef.value?.tooltipRef

  return {
    width: element?.offsetWidth || 120,
    height: element?.offsetHeight || 48,
  }
}

function positionTooltip(mouseX: number, mouseY: number) {
  const host = wrapperRef.value
  if (!host) return

  const tooltipSize = getTooltipSize()
  const gap = 12
  const rightLeft = mouseX + gap
  const leftLeft = mouseX - tooltipSize.width - gap
  const upperTop = mouseY - tooltipSize.height - gap
  const lowerTop = mouseY + gap
  const nextLeft = rightLeft + tooltipSize.width <= host.clientWidth - 8 ? rightLeft : leftLeft
  const nextTop = upperTop >= 8 ? upperTop : lowerTop

  tooltip.left = Math.min(Math.max(nextLeft, 8), host.clientWidth - tooltipSize.width - 8)
  tooltip.top = Math.min(Math.max(nextTop, 8), props.height - tooltipSize.height - 8)
}

function updateTooltip(index: number | null, mouseX: number, mouseY: number) {
  const primary = getPrimarySeries()
  if (!primary || index == null) {
    tooltip.visible = false
    return
  }

  const point = primary.data[index]
  if (!point) {
    tooltip.visible = false
    return
  }

  positionTooltip(mouseX, mouseY)
  tooltip.time = props.xFormatter(point.x)
  tooltip.items = props.series
    .map((item) => {
      const value = item.data[index]?.y
      if (value == null) return null

      return {
        title: item.title,
        value: props.valueFormatter(value, item),
        color: item.color,
      }
    })
    .filter((item): item is ChartTooltipItem => item != null)
  tooltip.visible = tooltip.items.length > 0
}

function handleMouseMove(event: MouseEvent) {
  const u = chart.value
  const host = wrapperRef.value
  if (!u || !host) return

  const rect = host.getBoundingClientRect()
  const mouseX = event.clientX - rect.left
  const mouseY = event.clientY - rect.top
  const plotLeft = u.bbox.left / uPlot.pxRatio
  const plotTop = u.bbox.top / uPlot.pxRatio
  const plotWidth = u.bbox.width / uPlot.pxRatio
  const plotHeight = u.bbox.height / uPlot.pxRatio

  if (
    mouseX < plotLeft ||
    mouseX > plotLeft + plotWidth ||
    mouseY < plotTop ||
    mouseY > plotTop + plotHeight
  ) {
    hideTooltip()
    return
  }

  const index = u.posToIdx(mouseX - plotLeft)

  updateTooltip(index, mouseX, mouseY)
}

function hideTooltip() {
  tooltip.visible = false
}

function createOptions(width: number): uPlot.Options {
  const primary = getPrimarySeries()

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
      x: { time: false },
      y: { auto: true, range: (_u, min, max) => [0, Math.max(max, min + 1)] },
    },
    axes: [
      {
        show: true,
        scale: 'x',
        size: 24,
        gap: 4,
        ticks: { show: false },
        border: { show: false },
        grid: { show: false },
        values: (_u, values) =>
          values.map((value) => {
            const index = Math.round(value)
            const label = primary?.data[index]?.x
            return label ? label.slice(5) : ''
          }),
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
          stroke: colorMix(getResolvedColor('var(--border-color)'), 0.5),
          width: 1,
        },
      },
    ],
    series: [
      {},
      ...props.series.map((item) => {
        const fillColor = getResolvedColor(item.color)

        return {
          label: item.title,
          stroke: fillColor,
          fill: fillColor,
          width: 0,
          paths: uPlot.paths.bars?.({
            size: [0.58, Number.POSITIVE_INFINITY, 1],
            radius: [0.22, 0.22],
          }),
          points: { show: false },
        }
      }),
    ],
  }
}

function mountChart() {
  const host = chartRef.value
  const wrapper = wrapperRef.value
  if (!host || !wrapper) return

  chart.value?.destroy()
  chart.value = new uPlot(createOptions(wrapper.clientWidth), toUplotData(), host)
}

function handleThemeChange() {
  nextTick(mountChart)
}

watch(
  () => props.series,
  () => {
    if (!chart.value) return

    chart.value.setData(toUplotData())
  },
  { deep: true },
)

watch(
  () => [props.height, props.emptyText],
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
.bar-chart {
  position: relative;
  width: 100%;
  min-height: 160px;
}

.bar-chart-canvas {
  width: 100%;
  height: 100%;

  :deep(.uplot) {
    width: 100%;
    font-family: ui-sans-serif, system-ui, sans-serif;
  }

  :deep(.u-over) {
    cursor: default;
  }

  :deep(.u-axis) {
    color: var(--text-tertiary);
    font-size: 0.72rem;
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
