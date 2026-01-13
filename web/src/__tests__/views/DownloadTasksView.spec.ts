import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import DownloadTasksView from '@/views/DownloadTasksView.vue'
import api from '@/api'
import { createRouter, createMemoryHistory } from 'vue-router'

// Mock API
vi.mock('@/api', () => ({
  default: {
    download: {
      getJobList: vi.fn(),
      getTaskList: vi.fn(),
      resetTask: vi.fn(),
    },
  },
}))

// Mock Toast
vi.mock('@/utils/toast', () => ({
  toast: {
    show: vi.fn(),
  },
}))

describe('DownloadTasksView.vue', () => {
  const mockJobs = [
    { id: 1, job_name: 'Job 1', playlist_id: '123' },
    { id: 2, job_name: 'Job 2', playlist_id: '456' },
  ]

  const mockTasks = [
    {
      id: 1,
      music_title: 'Song 1',
      music_artist: 'Artist 1',
      status: 'completed',
      job_id: 1,
    },
    {
      id: 2,
      music_title: 'Song 2',
      music_artist: 'Artist 2',
      status: 'failed',
      error_message: 'Download error',
      job_id: 1,
    },
  ]

  let router: any

  beforeEach(async () => {
    vi.clearAllMocks()
    
    // Setup default API responses
    ;(api.download.getJobList as any).mockResolvedValue({
      success: true,
      data: { code: 200, data: { jobs: mockJobs } },
    })
    ;(api.download.getTaskList as any).mockResolvedValue({
      success: true,
      data: { code: 200, data: { tasks: mockTasks, total: 2 } },
    })
    ;(api.download.resetTask as any).mockResolvedValue({
      success: true,
      data: { code: 200 },
    })

    // Setup Router
    router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/download/tasks', component: DownloadTasksView },
      ],
    })
    router.push('/download/tasks')
    await router.isReady()
  })

  it('renders correctly and fetches initial data', async () => {
    const wrapper = mount(DownloadTasksView, {
      global: {
        plugins: [router],
      },
    })
    
    expect(api.download.getJobList).toHaveBeenCalled()
    expect(api.download.getTaskList).toHaveBeenCalledWith(expect.objectContaining({
      page: 1,
      limit: 20,
    }))

    await flushPromises()

    // Check rendered jobs in sidebar
    const jobItems = wrapper.findAll('.config-nav-item')
    expect(jobItems.length).toBe(mockJobs.length + 1)
    expect(wrapper.text()).toContain('Job 1')
    expect(wrapper.text()).toContain('Job 2')

    // Check rendered tasks
    const taskItems = wrapper.findAll('.result-item')
    expect(taskItems.length).toBe(mockTasks.length)
    expect(wrapper.text()).toContain('Song 1')
    expect(wrapper.text()).toContain('Song 2')
  })

  it('handles search and filtering', async () => {
    const wrapper = mount(DownloadTasksView, {
      global: {
        plugins: [router],
      },
    })
    await flushPromises()

    const searchInput = wrapper.find('input.search-input')
    await searchInput.setValue('test keyword')
    
    const searchButton = wrapper.find('button.btn-primary')
    await searchButton.trigger('click')
    
    // Wait for router and watchers
    await flushPromises()

    expect(api.download.getTaskList).toHaveBeenLastCalledWith(expect.objectContaining({
      keyword: 'test keyword',
    }))
    expect(router.currentRoute.value.query.keyword).toBe('test keyword')
  })

  it('handles status filtering', async () => {
    const wrapper = mount(DownloadTasksView, {
      global: {
        plugins: [router],
      },
    })
    await flushPromises()

    const select = wrapper.find('select.input')
    await select.setValue('failed')
    await select.trigger('change')
    
    await flushPromises()

    expect(api.download.getTaskList).toHaveBeenLastCalledWith(expect.objectContaining({
      status: 'failed',
    }))
  })

  it('handles job selection', async () => {
    const wrapper = mount(DownloadTasksView, {
      global: {
        plugins: [router],
      },
    })
    await flushPromises()

    // Click on the first job (Job 1)
    const jobButtons = wrapper.findAll('.config-nav-item')
    await jobButtons[1].trigger('click')
    
    await flushPromises()

    expect(api.download.getTaskList).toHaveBeenLastCalledWith(expect.objectContaining({
      job_id: 1, // activeJobId.value is set to job.id which is 1
    }))
    expect(Number(router.currentRoute.value.query.job_id)).toBe(1)
  })
  
  it('resets task status', async () => {
    const wrapper = mount(DownloadTasksView, {
      global: {
        plugins: [router],
      },
    })
    await flushPromises()

    const failedTask = mockTasks.find(t => t.status === 'failed')
    const taskItems = wrapper.findAll('.result-item')
    // Find the task item that corresponds to the failed task
    // mockTasks order: [completed, failed]
    // index 1
    const failedTaskItem = taskItems[1]
    const resetButton = failedTaskItem.find('button.btn-secondary')
    
    expect(resetButton.exists()).toBe(true)

    await resetButton.trigger('click')

    expect(api.download.resetTask).toHaveBeenCalledWith(failedTask?.id)
    await flushPromises()
    
    expect(failedTask?.status).toBe('pending')
  })
})

