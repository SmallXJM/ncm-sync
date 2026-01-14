import { ref, watch, type Ref } from 'vue'
import { useRoute, useRouter, type RouteLocationNormalizedLoaded } from 'vue-router'

export const MUSIC_QUERY_STORAGE_KEY = 'music_view_query'

export type MusicStatus =
  | 'pending'
  | 'downloading'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'cancelled'

export type MusicQueryRaw = Record<string, string | string[]>

export interface MusicQueryParsed {
  jobId: number
  keyword: string
  status: MusicStatus | ''
  page: number
}

export interface MusicQueryStateRefs {
  activeJobId: Ref<number>
  searchKeyword: Ref<string>
  filterStatus: Ref<MusicStatus | ''>
  currentPage: Ref<number>
}

export interface UseMusicQueryOptions {
  storageKey?: string
  onRouteQueryChange?: () => void
}

// const allowedStatuses: MusicStatus[] = [
//   'pending',
//   'downloading',
//   'processing',
//   'completed',
//   'failed',
//   'cancelled',
// ]

// const allowedStatusSet = new Set<MusicStatus>(allowedStatuses)

const toSingleValue = (value: unknown) => {
  if (Array.isArray(value)) {
    if (value.length === 0) return undefined
    return value[0]
  }
  return value
}

export const parseMusicQuery = (query: RouteLocationNormalizedLoaded['query']): MusicQueryParsed => {
  const rawJobId = toSingleValue(query.subscription)
  const jobIdNumber =
    typeof rawJobId === 'string' || typeof rawJobId === 'number' ? Number(rawJobId) : NaN
  const jobId = Number.isFinite(jobIdNumber) && jobIdNumber >= 0 ? jobIdNumber : 0

  const rawKeyword = toSingleValue(query.keyword)
  const keyword = typeof rawKeyword === 'string' ? rawKeyword : ''

  const rawStatus = toSingleValue(query.status)
  const statusValue = typeof rawStatus === 'string' ? rawStatus : ''
  const status = statusValue as MusicStatus

  const rawPage = toSingleValue(query.page)
  const pageNumber =
    typeof rawPage === 'string' || typeof rawPage === 'number' ? Number(rawPage) : NaN
  const page = Number.isFinite(pageNumber) && pageNumber > 0 ? pageNumber : 1

  return {
    jobId,
    keyword,
    status,
    page,
  }
}

export const buildMusicQueryFromState = (
  state: MusicQueryParsed,
  baseQuery: RouteLocationNormalizedLoaded['query'],
): RouteLocationNormalizedLoaded['query'] => {
  const query: RouteLocationNormalizedLoaded['query'] = { ...baseQuery }

  if (state.jobId === 0) {
    delete query.subscription
  } else {
    query.subscription = String(state.jobId)
  }

  if (!state.keyword) {
    delete query.keyword
  } else {
    query.keyword = state.keyword
  }

  if (!state.status) {
    delete query.status
  } else {
    query.status = state.status
  }

  if (state.page === 1) {
    delete query.page
  } else {
    query.page = String(state.page)
  }

  return query
}

export const saveMusicQueryToStorage = (
  rawQuery: RouteLocationNormalizedLoaded['query'],
  storageKey = MUSIC_QUERY_STORAGE_KEY,
) => {
  if (typeof window === 'undefined') return
  try {
    const plainQuery: MusicQueryRaw = {}
    Object.keys(rawQuery).forEach((key) => {
      const value = rawQuery[key]
      if (Array.isArray(value)) {
        plainQuery[key] = value.map((v) => String(v))
      } else if (value != null) {
        plainQuery[key] = String(value)
      }
    })
    window.sessionStorage.setItem(storageKey, JSON.stringify(plainQuery))
  } catch {
  }
}

export const getStoredMusicQuery = (
  storageKey = MUSIC_QUERY_STORAGE_KEY,
): MusicQueryRaw | undefined => {
  if (typeof window === 'undefined') return undefined
  try {
    const raw = window.sessionStorage.getItem(storageKey)
    if (!raw) return undefined
    const parsed = JSON.parse(raw)
    if (!parsed || typeof parsed !== 'object') return undefined
    const result: MusicQueryRaw = {}
    Object.keys(parsed).forEach((key) => {
      const value = parsed[key]
      if (Array.isArray(value)) {
        result[key] = value.map((v) => String(v))
      } else if (value != null) {
        result[key] = String(value)
      }
    })
    return result
  } catch {
    return undefined
  }
}

export const useMusicQuery = (options: UseMusicQueryOptions = {}) => {
  const route = useRoute()
  const router = useRouter()
  const storageKey = options.storageKey ?? MUSIC_QUERY_STORAGE_KEY

  const activeJobId = ref(0)
  const searchKeyword = ref('')
  const filterStatus = ref<MusicStatus | ''>('')
  const currentPage = ref(1)

  const syncStateFromQuery = () => {
    const parsed = parseMusicQuery(route.query)
    activeJobId.value = parsed.jobId
    searchKeyword.value = parsed.keyword
    filterStatus.value = parsed.status
    currentPage.value = parsed.page
  }

  syncStateFromQuery()

  const updateUrl = () => {
    const nextQuery = buildMusicQueryFromState(
      {
        jobId: activeJobId.value,
        keyword: searchKeyword.value,
        status: filterStatus.value,
        page: currentPage.value,
      },
      route.query,
    )
    router.push({ query: nextQuery })
  }

  const saveToStorage = () => {
    saveMusicQueryToStorage(route.query, storageKey)
  }

  watch(
    () => route.query,
    () => {
      syncStateFromQuery()
      if (options.onRouteQueryChange) {
        options.onRouteQueryChange()
      }
    },
    { deep: true },
  )

  return {
    activeJobId,
    searchKeyword,
    filterStatus,
    currentPage,
    updateUrl,
    saveToStorage,
    getStoredQuery: () => getStoredMusicQuery(storageKey),
  }
}

