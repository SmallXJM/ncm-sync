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

    <ChartMarker
      v-for="item in markers"
      :key="item.key"
      :visible="tooltip.visible"
      :left="item.left"
      :top="item.top"
      :color="item.color"
    />

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
import ChartMarker from './ChartMarker.vue'
import ChartTooltip from './ChartTooltip.vue'
import {
  COMPACT_CHART_PADDING,
  colorMix,
  createHiddenChartCursor,
  createHiddenChartLegend,
  createHiddenXAxis,
  createHorizontalGridYAxis,
  findIndexByTimestamp,
  formatTimestamp,
  getFloatingTooltipPosition,
  getPlotBounds,
  getPointPosition,
  getRelativeMousePosition,
  getTooltipElementSize,
  getZeroBasedYRange,
  hasChartData,
  resolveCssColor,
  toAlignedChartData,
  watchChartTheme,
  type ChartTooltipItem,
  type TrendChartSeries,
} from './chartUtils'
import 'uplot/dist/uPlot.min.css'

interface MarkerState {
  key: string
  left: number
  top: number
  color: string
}

const props = withDefaults(
  defineProps<{
    series: TrendChartSeries[]
    height?: number
    emptyText?: string
    valueFormatter?: (value: number, series: TrendChartSeries) => string
    timeFormatter?: (timestampSeconds: number) => string
  }>(),
  {
    height: 220,
    emptyText: '暂无数据',
    valueFormatter: (value: number) => String(value),
    timeFormatter: formatTimestamp,
  },
)

const wrapperRef = ref<HTMLElement | null>(null)
const chartRef = ref<HTMLElement | null>(null)
const tooltipComponentRef = ref<InstanceType<typeof ChartTooltip> | null>(null)
const chart = ref<uPlot | null>(null)
const anchoredTimestamp = ref<number | null>(null)
const tooltip = reactive({
  visible: false,
  left: 0,
  top: 0,
  time: '',
  items: [] as ChartTooltipItem[],
})
const markers = reactive<MarkerState[]>([])

let resizeObserver: ResizeObserver | null = null
let stopThemeWatch: (() => void) | null = null

const hasData = computed(() => hasChartData(props.series))

function getResolvedColor(color: string): string {
  return resolveCssColor(color, wrapperRef.value)
}

function toUplotData(): uPlot.AlignedData {
  return toAlignedChartData(props.series, (point) => point.x / 1000)
}

function syncMarkers() {
  markers.splice(
    0,
    markers.length,
    ...props.series.map((item) => ({
      key: item.key,
      left: 0,
      top: 0,
      color: item.color,
    })),
  )
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
  if (timestamp == null) {
    tooltip.visible = false
    return
  }

  const pointStates = props.series
    .map((item, seriesIndex) => {
      const value = u.data[seriesIndex + 1]?.[index]
      if (value == null) return null

      return {
        series: item,
        value,
        position: getPointPosition(u, timestamp, value),
      }
    })
    .filter((item): item is NonNullable<typeof item> => item != null)

  if (pointStates.length === 0) {
    tooltip.visible = false
    return
  }

  const primaryPointState = pointStates[0]
  if (!primaryPointState) {
    tooltip.visible = false
    return
  }

  const primaryPoint = primaryPointState.position
  const baseLeft = mouseX ?? primaryPoint.left
  const baseTop = mouseY ?? primaryPoint.top

  pointStates.forEach((item, index) => {
    if (!markers[index]) return

    markers[index].left = item.position.left
    markers[index].top = item.position.top
    markers[index].color = item.series.color
  })

  if (shouldUpdateTooltipPosition) {
    const position = getFloatingTooltipPosition({
      host,
      mouseX: baseLeft,
      mouseY: baseTop,
      tooltipSize: getTooltipElementSize(tooltipComponentRef.value?.tooltipRef ?? null),
      chartHeight: props.height,
    })

    tooltip.left = position.left
    tooltip.top = position.top
  }

  tooltip.time = props.timeFormatter(timestamp)
  tooltip.items = pointStates.map((item) => ({
    title: item.series.title,
    value: props.valueFormatter(item.value, item.series),
    color: item.series.color,
  }))
  tooltip.visible = true
}

function handleMouseMove(event: MouseEvent) {
  const u = chart.value
  const host = wrapperRef.value
  if (!u || !host) return

  const mousePosition = getRelativeMousePosition(event, host)
  const plotBounds = getPlotBounds(u)
  const index = u.posToIdx(mousePosition.left - plotBounds.left)

  if (index == null) return

  anchoredTimestamp.value = u.data[0]?.[index] ?? null
  updateTooltip(index, mousePosition.left, mousePosition.top)
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
  if (nextTimestamp == null) {
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
  return {
    width,
    height: props.height,
    padding: COMPACT_CHART_PADDING,
    cursor: createHiddenChartCursor(),
    legend: createHiddenChartLegend(),
    scales: {
      x: { time: true },
      y: { auto: true, range: getZeroBasedYRange },
    },
    axes: [
      createHiddenXAxis(),
      createHorizontalGridYAxis(getResolvedColor('var(--border-color)')),
    ],
    series: [
      {},
      ...props.series.map((item, index) => {
        const lineColor = getResolvedColor(item.color)

        return {
          label: item.title,
          stroke: lineColor,
          width: 1.5,
          paths: uPlot.paths.spline?.(),
          points: {
            show: false,
            size: 5,
            width: 1.5,
            stroke: lineColor,
            fill: getResolvedColor('var(--bg-surface)'),
          },
          fill:
            index === 0
              ? (u: uPlot) => {
                  const gradient = u.ctx.createLinearGradient(0, 0, 0, props.height)
                  gradient.addColorStop(1, colorMix(lineColor, 0.2))
                  return gradient
                }
              : undefined,
        }
      }),
    ],
  }
}

function mountChart() {
  const host = chartRef.value
  const wrapper = wrapperRef.value
  if (!host || !wrapper) return

  syncMarkers()
  chart.value?.destroy()
  chart.value = new uPlot(createOptions(wrapper.clientWidth), toUplotData(), host)
  refreshTooltip()
}

function handleThemeChange() {
  nextTick(mountChart)
}

watch(
  () => props.series,
  () => {
    if (!chart.value) return

    syncMarkers()
    chart.value.setData(toUplotData())
    nextTick(refreshTooltip)
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
      refreshTooltip()
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
