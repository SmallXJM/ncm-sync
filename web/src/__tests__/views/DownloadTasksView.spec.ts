import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import MusicView from '@/views/MusicView.vue'
import AppHeader from '@/layout/AppHeader.vue'
import api from '@/api'
import { createRouter, createMemoryHistory, type Router } from 'vue-router'

if (!window.matchMedia) {
  window.matchMedia = ((query: string) => {
    const mql = {
      matches: false,
      media: query,
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(),
    } as unknown as MediaQueryList
    return mql
  }) as unknown as typeof window.matchMedia
}

vi.mock('@/api', () => ({
  default: {
    download: {
      getJobList: vi.fn(),
      getTaskList: vi.fn(),
      resetTask: vi.fn(),
    },
  },
}))

vi.mock('@/utils/toast', () => ({
  toast: {
    show: vi.fn(),
  },
}))

describe('MusicView.vue + AppHeader breadcrumb', () => {
  const mockJobs = [
    { id: 1, job_name: 'Job 1', playlist_id: '123' },
    { id: 2, job_name: 'Job 2', playlist_id: '456' },
  ]

  const mockTasks = [
    {
      id: 1,
      music_id: '1001',
      music_title: 'Song 1',
      music_artist: 'Artist 1',
      music_album: 'Album 1',
      status: 'completed',
      file_path: 'E:\\Music\\Song1.mp3',
      job_id: 1,
      progress_flags: 0,
    },
    {
      id: 2,
      music_id: '1002',
      music_title: 'Song 2',
      music_artist: 'Artist 2',
      music_album: 'Album 2',
      status: 'failed',
      error_message: 'Download error',
      job_id: 1,
      progress_flags: 0,
    },
  ]

  let router: Router

  beforeEach(async () => {
    vi.clearAllMocks()

    const mockedApi = api as unknown as {
      download: {
        getJobList: ReturnType<typeof vi.fn>
        getTaskList: ReturnType<typeof vi.fn>
        resetTask: ReturnType<typeof vi.fn>
      }
    }

    mockedApi.download.getJobList.mockResolvedValue({
      success: true,
      data: { code: 200, data: { jobs: mockJobs } },
    })
    mockedApi.download.getTaskList.mockResolvedValue({
      success: true,
      data: { code: 200, data: { tasks: mockTasks, total: 40 } },
    })
    mockedApi.download.resetTask.mockResolvedValue({
      success: true,
      data: { code: 200 },
    })

    router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/music', name: 'music', component: MusicView, meta: { title: '音乐管理' } },
        {
          path: '/music/:taskId',
          name: 'music-detail',
          component: { template: '<div />' },
          meta: { title: '音乐详情', parent: { title: '音乐管理', to: '/music' } },
        },
      ],
    })
    router.push('/music')
    await router.isReady()
  })

  it('renders cards and fetches initial data', async () => {
    const wrapper = mount(MusicView, {
      global: {
        plugins: [router],
      },
    })

    expect(api.download.getJobList).toHaveBeenCalled()
    expect(api.download.getTaskList).toHaveBeenCalledWith(
      expect.objectContaining({
        page: 1,
        limit: 20,
      }),
    )

    await flushPromises()

    const cards = wrapper.findAll('.playlist-card')
    expect(cards.length).toBe(mockTasks.length)
    expect(wrapper.text()).toContain('Song 1')
    expect(wrapper.text()).toContain('Song 2')
  })

  it('navigates to detail route when clicking 详情', async () => {
    const wrapper = mount(MusicView, {
      global: {
        plugins: [router],
      },
    })
    await flushPromises()

    const firstCard = wrapper.findAll('.playlist-card')[0]
    const detailBtn = firstCard.find('button.btn-primary')
    await detailBtn.trigger('click')
    await flushPromises()

    expect(router.currentRoute.value.name).toBe('music-detail')
    expect(router.currentRoute.value.params.taskId).toBe('1')
  })

  it('renders breadcrumb and allows clicking parent to navigate back', async () => {
    await router.push('/music/1')
    await router.isReady()

    const wrapper = mount(AppHeader, {
      global: {
        plugins: [router],
      },
    })

    expect(wrapper.text()).toContain('音乐管理')
    expect(wrapper.text()).toContain('音乐详情')

    const parentLink = wrapper.find('button.breadcrumb-link')
    expect(parentLink.exists()).toBe(true)

    await parentLink.trigger('click')
    await flushPromises()

    expect(router.currentRoute.value.name).toBe('music')
  })
})
