import { describe, it, expect, beforeEach, vi } from 'vitest'
import { parseMusicQuery, buildMusicQueryFromState, saveMusicQueryToStorage, getStoredMusicQuery, type MusicQueryParsed } from '@/composables/useMusicQuery'

const createRouteQuery = (query: Record<string, unknown>) =>
  query as unknown as import('vue-router').RouteLocationNormalizedLoaded['query']

describe('useMusicQuery helpers', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    if (typeof window !== 'undefined') {
      window.sessionStorage.clear()
    }
  })

  it('parses valid query into typed state with defaults', () => {
    const query = createRouteQuery({
      job_id: '3',
      keyword: 'rock',
      status: 'downloading',
      page: '5',
    })

    const parsed = parseMusicQuery(query)

    expect(parsed).toEqual<MusicQueryParsed>({
      jobId: 3,
      keyword: 'rock',
      status: 'downloading',
      page: 5,
    })
  })

  it('applies defaults when query is missing or invalid', () => {
    const query = createRouteQuery({
      job_id: '-1',
      keyword: 123,
      status: 'unknown',
      page: '0',
    })

    const parsed = parseMusicQuery(query)

    expect(parsed.jobId).toBe(0)
    expect(parsed.keyword).toBe('')
    expect(parsed.status).toBe('completed')
    expect(parsed.page).toBe(1)
  })

  it('handles array values by taking the first element', () => {
    const query = createRouteQuery({
      job_id: ['4', '5'],
      keyword: ['a', 'b'],
      status: ['failed', 'completed'],
      page: ['2', '3'],
    })

    const parsed = parseMusicQuery(query)

    expect(parsed.jobId).toBe(4)
    expect(parsed.keyword).toBe('a')
    expect(parsed.status).toBe('failed')
    expect(parsed.page).toBe(2)
  })

  it('builds query from state and removes default values', () => {
    const base = createRouteQuery({
      job_id: '1',
      keyword: 'old',
      status: 'pending',
      page: '3',
      extra: 'keep',
    })

    const next = buildMusicQueryFromState(
      {
        jobId: 0,
        keyword: '',
        status: 'completed',
        page: 1,
      },
      base,
    )

    expect(next).toEqual(
      createRouteQuery({
        extra: 'keep',
      }),
    )
  })

  it('persists query to sessionStorage and reads it back', () => {
    const query = createRouteQuery({
      job_id: 2,
      keyword: 'test',
      status: 'completed',
      page: 3,
    })

    saveMusicQueryToStorage(query)
    const stored = getStoredMusicQuery()

    expect(stored).toEqual({
      job_id: '2',
      keyword: 'test',
      status: 'completed',
      page: '3',
    })
  })

  it('returns undefined when storage is not available or invalid', () => {
    const originalWindow = globalThis.window
    // @ts-expect-error override for test
    delete (globalThis as any).window

    const resultWithoutWindow = getStoredMusicQuery()
    expect(resultWithoutWindow).toBeUndefined()

    ;(globalThis as any).window = originalWindow

    if (typeof window !== 'undefined') {
      window.sessionStorage.setItem('music_view_query', 'not-json')
    }

    const resultInvalid = getStoredMusicQuery()
    expect(resultInvalid).toBeUndefined()
  })
})

