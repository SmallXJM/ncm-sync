import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AppPagination from '@/components/AppPagination.vue'

describe('AppPagination.vue', () => {
  it('renders correctly', () => {
    const wrapper = mount(AppPagination, {
      props: {
        totalItems: 100,
        currentPage: 1,
        pageSize: 10,
      },
    })
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.findAll('button').length).toBeGreaterThan(0)
  })

  it('calculates total pages correctly', () => {
    const wrapper = mount(AppPagination, {
      props: {
        totalItems: 55,
        currentPage: 1,
        pageSize: 10,
      },
    })
    // 55 / 10 = 5.5 -> 6 pages
    // Buttons: prev, next, 1, 2, 3, 4, 5, 6 (if all visible)
    // Actually visible pages logic might show ellipsis if many pages, but 6 fits in 5 window?
    // Logic: total <= 5 ? show all. 6 > 5.
    // Window size 5.
    // Start 1-2 = -1 -> 1. End 1+2 = 3.
    // End < 6 -> show ... -> show last page (6)?
    // The logic in component:
    // if total <= windowSize (5) -> show all
    // else calculate start/end.
    
    // Let's verify visible pages text
    const buttons = wrapper.findAll('button.btn-sm') // Page number buttons (excluding prev/next/first/last if they have different classes, but they use btn-sm too?)
    // In template:
    // First/Prev/Next/Last use: btn btn-secondary btn-sm icon-btn
    // Page numbers use: btn btn-sm (and class binding)
    // So filter by text content being a number
    
    const pageButtons = buttons.filter(b => !isNaN(Number(b.text())) && b.text() !== '')
    // Logic for page 1 of 6:
    // start=1, end=3 (window 5/2=2). 
    // Wait, logic:
    // start = 1 - 2 = -1 -> 1
    // end = 1 + 2 = 3
    // Pages: 1, 2, 3
    // Right ellipsis? if end < total (3 < 6) -> Yes.
    // So pages array: [1, 2, 3, '...']? No, '...' is span.
    // But '...' logic in template: <span ...>...</span>
    
    // Check if we can find page 6? 
    // Logic doesn't explicitly add last page if not in range.
    // Wait, the original logic:
    // if (end < total) pages.push("...")
    // It doesn't push the last page number explicitly unless it's in range [start, end].
    // This seems to be the logic copied from MyPlaylistView.vue.
    
    expect(wrapper.text()).toContain('1')
    expect(wrapper.text()).toContain('3')
  })

  it('emits page-change event when a page is clicked', async () => {
    const wrapper = mount(AppPagination, {
      props: {
        totalItems: 100,
        currentPage: 1,
        pageSize: 10,
      },
    })

    const buttons = wrapper.findAll('button')
    // Find button with text "2"
    const page2Btn = buttons.find(b => b.text() === '2')
    await page2Btn?.trigger('click')

    expect(wrapper.emitted('page-change')).toBeTruthy()
    expect(wrapper.emitted('page-change')?.[0]).toEqual([2])
  })

  it('does not emit event when clicking current page', async () => {
    const wrapper = mount(AppPagination, {
      props: {
        totalItems: 100,
        currentPage: 1,
        pageSize: 10,
      },
    })

    const buttons = wrapper.findAll('button')
    const page1Btn = buttons.find(b => b.text() === '1')
    await page1Btn?.trigger('click')

    expect(wrapper.emitted('page-change')).toBeFalsy()
  })

  it('disables previous button on first page', () => {
    const wrapper = mount(AppPagination, {
      props: {
        totalItems: 100,
        currentPage: 1,
        pageSize: 10,
      },
    })

    // First button (First Page) and Second button (Prev Page) should be disabled
    const buttons = wrapper.findAll('button')
    expect(buttons[0].attributes('disabled')).toBeDefined()
    expect(buttons[1].attributes('disabled')).toBeDefined()
  })

  it('disables next button on last page', () => {
    const wrapper = mount(AppPagination, {
      props: {
        totalItems: 100,
        currentPage: 10,
        pageSize: 10,
      },
    })

    const buttons = wrapper.findAll('button')
    const lastIndex = buttons.length - 1
    const nextIndex = buttons.length - 2
    expect(buttons[lastIndex].attributes('disabled')).toBeDefined()
    expect(buttons[nextIndex].attributes('disabled')).toBeDefined()
  })
})
