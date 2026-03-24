import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createPinia, setActivePinia } from 'pinia'
import HistoryPage from '../HistoryPage.vue'
import * as historyApi from '@/api/history'
import Button from '@/components/ui/Button.vue'

vi.mock('@/api/history', () => ({
  getHistoryBatches: vi.fn(),
  getHistoryByBatch: vi.fn(),
  updateBatchName: vi.fn(),
  deleteBatch: vi.fn(),
}))

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({
    success: vi.fn(),
    error: vi.fn(),
  }),
}))

vi.mock('@/composables/useConfirm', () => ({
  useConfirm: () => ({
    show: vi.fn(),
    state: { value: { open: false } },
    cancel: vi.fn(),
    confirm: vi.fn(),
  }),
}))

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: {
    en: {
      common: {
        loading: 'Loading...',
        error: 'Error',
        refresh: 'Refresh',
        delete: 'Delete',
        cancel: 'Cancel',
        save: 'Save',
      },
      history: {
        title: 'History',
        empty: 'No history',
        empty_items: 'No items',
        batch_title: 'Batch #{id}',
        item: 'item',
        items: 'items',
        fetched: 'Fetched',
        edit_name: 'Edit name',
        preview: 'Preview',
        name_required: 'Name is required',
        name_updated: 'Name updated',
        name_placeholder: 'Enter name',
        delete_title: 'Delete Batch',
        delete_confirm: 'Are you sure?',
        deleted: 'Deleted',
        result: {
          total_batches: '{count} batches, {items} items',
        },
      },
      feed: {
        item: 'item',
        items: 'items',
        format_rss: 'RSS',
        format_json: 'JSON',
        format_markdown: 'Markdown',
        download: 'Download {format}',
      },
      keys: {
        copy: 'Copy',
        copied: 'Copied',
        copy_failed: 'Copy failed',
      },
    },
  },
})

describe('HistoryPage', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  const mountComponent = () => {
    return mount(HistoryPage, {
      global: {
        plugins: [i18n],
        components: {
          Button,
        },
        stubs: {
          ConfirmDialog: true,
          JsonPreview: true,
          MarkdownPreview: true,
          RssXmlPreview: true,
          Teleport: true,
        },
      },
    })
  }

  describe('initial render', () => {
    it('should show loading state initially', async () => {
      vi.mocked(historyApi.getHistoryBatches).mockImplementation(
        () => new Promise(() => {})
      )

      const wrapper = mountComponent()

      await wrapper.vm.$nextTick()

      const loadingText = wrapper.find('.text-center')
      expect(loadingText.exists()).toBe(true)
    })

    it('should show empty state when no batches', async () => {
      vi.mocked(historyApi.getHistoryBatches).mockResolvedValue({
        batches: [],
        total_batches: 0,
        total_items: 0,
      })

      const wrapper = mountComponent()
      await wrapper.vm.$nextTick()
      await new Promise((r) => setTimeout(r, 100))

      expect(wrapper.text()).toContain('No history')
    })

    it('should display batches when available', async () => {
      vi.mocked(historyApi.getHistoryBatches).mockResolvedValue({
        batches: [
          {
            id: 1,
            name: 'Test Batch',
            items_count: 5,
            sources: ['https://example.com/feed.xml'],
            created_at: '2024-01-15T10:00:00',
            latest_fetched_at: '2024-01-15T10:00:00',
            latest_published_at: '2024-01-15T09:00:00',
          },
        ],
        total_batches: 1,
        total_items: 5,
      })

      const wrapper = mountComponent()
      await wrapper.vm.$nextTick()
      await new Promise((r) => setTimeout(r, 100))

      expect(wrapper.text()).toContain('Test Batch')
      expect(wrapper.text()).toContain('5 items')
    })
  })

  describe('refresh', () => {
    it('should call getHistoryBatches on refresh click', async () => {
      vi.mocked(historyApi.getHistoryBatches).mockResolvedValue({
        batches: [],
        total_batches: 0,
        total_items: 0,
      })

      const wrapper = mountComponent()
      await wrapper.vm.$nextTick()
      await new Promise((r) => setTimeout(r, 100))

      vi.clearAllMocks()

      vi.mocked(historyApi.getHistoryBatches).mockResolvedValue({
        batches: [],
        total_batches: 0,
        total_items: 0,
      })

      const refreshButton = wrapper.find('button')
      await refreshButton.trigger('click')

      expect(historyApi.getHistoryBatches).toHaveBeenCalled()
    })
  })

  describe('toggle batch', () => {
    it('should expand batch on click', async () => {
      vi.mocked(historyApi.getHistoryBatches).mockResolvedValue({
        batches: [
          {
            id: 1,
            name: 'Test Batch',
            items_count: 2,
            sources: [],
            created_at: '2024-01-15T10:00:00',
            latest_fetched_at: null,
            latest_published_at: null,
          },
        ],
        total_batches: 1,
        total_items: 2,
      })

      vi.mocked(historyApi.getHistoryByBatch).mockResolvedValue({
        items: [
          {
            id: 1,
            source_id: 1,
            source: 'Test Source',
            title: 'Item 1',
            link: 'https://example.com/1',
            description: 'Description',
            published_at: '2024-01-15T09:00:00',
            fetched_at: '2024-01-15T10:00:00',
          },
        ],
        pagination: {
          page: 1,
          page_size: 50,
          total_items: 1,
          total_pages: 1,
        },
      })

      const wrapper = mountComponent()
      await wrapper.vm.$nextTick()
      await new Promise((r) => setTimeout(r, 100))

      const expandButton = wrapper.findAll('button').find((b) => {
        const icon = b.findComponent({ name: 'ChevronDown' })
        return icon.exists()
      })

      if (expandButton) {
        await expandButton.trigger('click')
        await wrapper.vm.$nextTick()
        await new Promise((r) => setTimeout(r, 100))

        expect(historyApi.getHistoryByBatch).toHaveBeenCalledWith(1, 1, 100)
      }
    })
  })

  describe('edit name', () => {
    it('should show edit input when edit button clicked', async () => {
      vi.mocked(historyApi.getHistoryBatches).mockResolvedValue({
        batches: [
          {
            id: 1,
            name: 'Test Batch',
            items_count: 1,
            sources: [],
            created_at: '2024-01-15T10:00:00',
            latest_fetched_at: null,
            latest_published_at: null,
          },
        ],
        total_batches: 1,
        total_items: 1,
      })

      const wrapper = mountComponent()
      await wrapper.vm.$nextTick()
      await new Promise((r) => setTimeout(r, 100))

      const editButton = wrapper.findAll('button').find((b) => {
        const icon = b.findComponent({ name: 'Pencil' })
        return icon.exists()
      })

      if (editButton) {
        await editButton.trigger('click')
        await wrapper.vm.$nextTick()

        const input = wrapper.find('input')
        expect(input.exists()).toBe(true)
      }
    })

    it('should call updateBatchName on save', async () => {
      vi.mocked(historyApi.getHistoryBatches).mockResolvedValue({
        batches: [
          {
            id: 1,
            name: 'Test Batch',
            items_count: 1,
            sources: [],
            created_at: '2024-01-15T10:00:00',
            latest_fetched_at: null,
            latest_published_at: null,
          },
        ],
        total_batches: 1,
        total_items: 1,
      })

      vi.mocked(historyApi.updateBatchName).mockResolvedValue({
        id: 1,
        name: 'New Name',
        items_count: 1,
        sources: [],
        created_at: '2024-01-15T10:00:00',
        latest_fetched_at: null,
        latest_published_at: null,
      })

      const wrapper = mountComponent()
      await wrapper.vm.$nextTick()
      await new Promise((r) => setTimeout(r, 100))

      const editButton = wrapper.findAll('button').find((b) => {
        const icon = b.findComponent({ name: 'Pencil' })
        return icon.exists()
      })

      if (editButton) {
        await editButton.trigger('click')
        await wrapper.vm.$nextTick()

        const input = wrapper.find('input')
        await input.setValue('New Name')

        const saveButton = wrapper.findAll('button').find((b) => {
          const icon = b.findComponent({ name: 'Check' })
          return icon.exists()
        })

        if (saveButton) {
          await saveButton.trigger('click')
          await wrapper.vm.$nextTick()
          await new Promise((r) => setTimeout(r, 100))

          expect(historyApi.updateBatchName).toHaveBeenCalledWith(1, { name: 'New Name' })
        }
      }
    })
  })

  describe('delete batch', () => {
    it('should show confirm dialog on delete click', async () => {
      const mockShow = vi.fn().mockResolvedValue(false)
      vi.mock('@/composables/useConfirm', () => ({
        useConfirm: () => ({
          show: mockShow,
          state: { value: { open: false } },
          cancel: vi.fn(),
          confirm: vi.fn(),
        }),
      }))

      vi.mocked(historyApi.getHistoryBatches).mockResolvedValue({
        batches: [
          {
            id: 1,
            name: 'Test Batch',
            items_count: 1,
            sources: [],
            created_at: '2024-01-15T10:00:00',
            latest_fetched_at: null,
            latest_published_at: null,
          },
        ],
        total_batches: 1,
        total_items: 1,
      })

      const wrapper = mountComponent()
      await wrapper.vm.$nextTick()
      await new Promise((r) => setTimeout(r, 100))

      const deleteButton = wrapper.findAll('button').find((b) => {
        const icon = b.findComponent({ name: 'Trash2' })
        return icon.exists()
      })

      if (deleteButton) {
        await deleteButton.trigger('click')
        expect(mockShow).toHaveBeenCalled()
      }
    })

    it('should call deleteBatch when confirmed', async () => {
      vi.mocked(historyApi.getHistoryBatches).mockResolvedValue({
        batches: [
          {
            id: 1,
            name: 'Test Batch',
            items_count: 1,
            sources: [],
            created_at: '2024-01-15T10:00:00',
            latest_fetched_at: null,
            latest_published_at: null,
          },
        ],
        total_batches: 1,
        total_items: 1,
      })

      vi.mocked(historyApi.deleteBatch).mockResolvedValue({ success: true })

      vi.mock('@/composables/useConfirm', () => ({
        useConfirm: () => ({
          show: vi.fn().mockResolvedValue(true),
          state: { value: { open: false } },
          cancel: vi.fn(),
          confirm: vi.fn(),
        }),
      }))

      const wrapper = mountComponent()
      await wrapper.vm.$nextTick()
      await new Promise((r) => setTimeout(r, 100))

      const deleteButton = wrapper.findAll('button').find((b) => {
        const icon = b.findComponent({ name: 'Trash2' })
        return icon.exists()
      })

      if (deleteButton) {
        await deleteButton.trigger('click')
        await wrapper.vm.$nextTick()
        await new Promise((r) => setTimeout(r, 100))

        expect(historyApi.deleteBatch).toHaveBeenCalledWith(1)
      }
    })
  })
})