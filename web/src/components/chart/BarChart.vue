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
  COMPACT_CHART_PADDING,
  createHiddenChartCursor,
  createHiddenChartLegend,
  createHiddenXAxis,
  createHorizontalGridYAxis,
  getFloatingTooltipPosition,
  getPlotBounds,
  getRelativeMousePosition,
  getTooltipElementSize,
  getZeroBasedYRange,
  hasChartData,
  isPointInPlot,
  resolveCssColor,
  toAlignedChartData,
  watchChartTheme,
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
let stopThemeWatch: (() => void) | null = null

const hasData = computed(() => hasChartData(props.series))

function getPrimarySeries(): BarChartSeries | null {
  return props.series[0] ?? null
}

function getResolvedColor(color: string): string {
  return resolveCssColor(color, wrapperRef.value)
}

function toUplotData(): uPlot.AlignedData {
  return toAlignedChartData(props.series, (_point, index) => index)
}

function updateTooltipPosition(mouseX: number, mouseY: number) {
  const host = wrapperRef.value
  if (!host) return

  const position = getFloatingTooltipPosition({
    host,
    mouseX,
    mouseY,
    tooltipSize: getTooltipElementSize(tooltipComponentRef.value?.tooltipRef ?? null),
    chartHeight: props.height,
  })

  tooltip.left = position.left
  tooltip.top = position.top
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

  updateTooltipPosition(mouseX, mouseY)
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

  const mousePosition = getRelativeMousePosition(event, host)
  const plotBounds = getPlotBounds(u)

  if (!isPointInPlot(mousePosition, plotBounds)) {
    hideTooltip()
    return
  }

  const index = u.posToIdx(mousePosition.left - plotBounds.left)

  updateTooltip(index, mousePosition.left, mousePosition.top)
}

function hideTooltip() {
  tooltip.visible = false
}

function createOptions(width: number): uPlot.Options {
  return {
    width,
    height: props.height,
    padding: COMPACT_CHART_PADDING,
    cursor: createHiddenChartCursor(),
    legend: createHiddenChartLegend(),
    scales: {
      x: {
        time: false,
        range: (_u, min, max) => [min - 0.5, max + 0.5],
      },
      y: { auto: true, range: getZeroBasedYRange },
    },
    axes: [
      createHiddenXAxis(),
      createHorizontalGridYAxis(getResolvedColor('var(--border-color)')),
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

    stopThemeWatch = watchChartTheme(handleThemeChange)
  })
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  stopThemeWatch?.()
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
