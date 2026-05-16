import uPlot from 'uplot'

export interface TrendChartPoint {
  x: number
  y: number
}

export interface TrendChartSeries {
  key: string
  title: string
  color: string
  data: TrendChartPoint[]
}

export interface ChartTooltipItem {
  title: string
  value: string
  color: string
}

export interface BarChartPoint {
  x: string
  y: number
}

export interface BarChartSeries {
  key: string
  title: string
  color: string
  data: BarChartPoint[]
}

export interface ChartTooltipSize {
  width: number
  height: number
}

export interface ChartTooltipPositionOptions {
  host: HTMLElement
  mouseX: number
  mouseY: number
  tooltipSize: ChartTooltipSize
  chartHeight: number
  gap?: number
  padding?: number
}

export interface ChartPoint {
  left: number
  top: number
}

export interface ChartPlotBounds {
  left: number
  top: number
  width: number
  height: number
}

export const COMPACT_CHART_PADDING = [8, 0, 8, 0] as uPlot.Padding

export function hasChartData(series: ReadonlyArray<{ data: ReadonlyArray<unknown> }>): boolean {
  return series.some((item) => item.data.length > 0)
}

export function toAlignedChartData<TPoint extends { y: number }>(
  series: ReadonlyArray<{ data: ReadonlyArray<TPoint> }>,
  getXValue: (point: TPoint, index: number) => number,
): uPlot.AlignedData {
  const xValues = series[0]?.data.map(getXValue) ?? []
  const yValues = series.map((item) => item.data.map((point) => point.y))

  return [xValues, ...yValues] as uPlot.AlignedData
}

export function createHiddenChartCursor(): uPlot.Cursor {
  return {
    x: false,
    y: false,
    drag: { x: false, y: false },
    points: { show: false },
  }
}

export function createHiddenChartLegend(): uPlot.Legend {
  return {
    show: false,
  }
}

export function createHiddenXAxis(): uPlot.Axis {
  return {
    show: false,
    scale: 'x',
  }
}

export function createHorizontalGridYAxis(borderColor: string): uPlot.Axis {
  return {
    show: true,
    scale: 'y',
    size: 0,
    ticks: { show: false },
    border: { show: false },
    values: (_u, values) => values.map(() => ''),
    grid: {
      show: true,
      stroke: colorMix(borderColor, 0.5),
      width: 1,
    },
  }
}

export function getZeroBasedYRange(_u: uPlot, min: number, max: number): [number, number] {
  return [0, Math.max(max, min + 1)]
}

export function resolveCssColor(value: string, host: HTMLElement | null): string {
  if (!host || !value.startsWith('var(')) return value

  const name = value.slice(4, -1).trim()
  return getComputedStyle(host).getPropertyValue(name).trim() || value
}

export function colorMix(color: string, alpha: number): string {
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

export function getTooltipElementSize(
  element: HTMLElement | null,
  fallback: ChartTooltipSize = { width: 120, height: 48 },
): ChartTooltipSize {
  return {
    width: element?.offsetWidth || fallback.width,
    height: element?.offsetHeight || fallback.height,
  }
}

export function getFloatingTooltipPosition({
  host,
  mouseX,
  mouseY,
  tooltipSize,
  chartHeight,
  gap = 12,
  padding = 8,
}: ChartTooltipPositionOptions): ChartPoint {
  const rightLeft = mouseX + gap
  const leftLeft = mouseX - tooltipSize.width - gap
  const upperTop = mouseY - tooltipSize.height - gap
  const lowerTop = mouseY + gap
  const nextLeft =
    rightLeft + tooltipSize.width <= host.clientWidth - padding ? rightLeft : leftLeft
  const nextTop =
    lowerTop + tooltipSize.height <= chartHeight - padding ? lowerTop : upperTop
  const maxLeft = Math.max(padding, host.clientWidth - tooltipSize.width - padding)
  const maxTop = Math.max(padding, chartHeight - tooltipSize.height - padding)

  return {
    left: Math.min(Math.max(nextLeft, padding), maxLeft),
    top: Math.min(Math.max(nextTop, padding), maxTop),
  }
}

export function getRelativeMousePosition(event: MouseEvent, host: HTMLElement): ChartPoint {
  const rect = host.getBoundingClientRect()

  return {
    left: event.clientX - rect.left,
    top: event.clientY - rect.top,
  }
}

export function getPlotBounds(u: uPlot): ChartPlotBounds {
  return {
    left: u.bbox.left / uPlot.pxRatio,
    top: u.bbox.top / uPlot.pxRatio,
    width: u.bbox.width / uPlot.pxRatio,
    height: u.bbox.height / uPlot.pxRatio,
  }
}

export function isPointInPlot(point: ChartPoint, bounds: ChartPlotBounds): boolean {
  return (
    point.left >= bounds.left &&
    point.left <= bounds.left + bounds.width &&
    point.top >= bounds.top &&
    point.top <= bounds.top + bounds.height
  )
}

export function watchChartTheme(onChange: () => void): () => void {
  const themeObserver = new MutationObserver(onChange)
  themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['class'],
  })

  const colorSchemeMq = window.matchMedia('(prefers-color-scheme: dark)')
  colorSchemeMq.addEventListener('change', onChange)

  return () => {
    themeObserver.disconnect()
    colorSchemeMq.removeEventListener('change', onChange)
  }
}

export function formatTimestamp(seconds: number): string {
  if (!Number.isFinite(seconds)) return '--'

  return new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(new Date(seconds * 1000))
}

export function findIndexByTimestamp(u: uPlot, timestamp: number): number | null {
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

export function getPointPosition(u: uPlot, timestamp: number, value: number) {
  const plotBounds = getPlotBounds(u)

  return {
    left: plotBounds.left + u.valToPos(timestamp, 'x'),
    top: plotBounds.top + u.valToPos(value, 'y'),
  }
}
