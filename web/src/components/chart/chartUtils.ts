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
  const plotLeft = u.bbox.left / uPlot.pxRatio
  const plotTop = u.bbox.top / uPlot.pxRatio

  return {
    left: plotLeft + u.valToPos(timestamp, 'x'),
    top: plotTop + u.valToPos(value, 'y'),
  }
}
