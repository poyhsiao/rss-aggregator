import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import ArticlePreviewDialog from '../ArticlePreviewDialog.vue'
import Button from '@/components/ui/Button.vue'

vi.mock('@/composables/useArticlePreview', () => ({
  useArticlePreview: () => ({
    fetchPreview: vi.fn(),
    reset: vi.fn(),
    content: { value: '' },
    title: { value: null },
    loading: { value: false },
    error: { value: null },
    source: { value: null },
  }),
}))

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({
    success: vi.fn(),
    error: vi.fn(),
  }),
}))

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: {
    en: {
      preview: {
        title: 'Article Preview',
        loading: 'Loading...',
        error: 'Failed to load content',
        open_in_new: 'Open in new tab',
        close: 'Close',
      },
      common: {
        loading: 'Loading...',
        error: 'Error',
      },
      feed: {
        view_source: 'Source',
        view_preview: 'Preview',
      },
    },
  },
})

describe('ArticlePreviewDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const mountComponent = (props = {}) => {
    return mount(ArticlePreviewDialog, {
      props: {
        open: true,
        url: 'https://example.com/article',
        ...props,
      },
      global: {
        plugins: [i18n],
        components: {
          Button,
        },
        stubs: {
          Dialog: {
            template: '<div class="dialog-mock" v-if="open"><slot /></div>',
            props: ['open', 'size'],
          },
          MarkdownPreview: {
            template: '<div class="markdown-preview-mock">{{ content }}</div>',
            props: ['content'],
          },
          Teleport: true,
        },
      },
    })
  }

  describe('initial state', () => {
    it('should render when open', () => {
      const wrapper = mountComponent({ open: true })
      expect(wrapper.find('.dialog-mock').exists()).toBe(true)
    })

    it('should not render when closed', () => {
      const wrapper = mountComponent({ open: false })
      expect(wrapper.find('.dialog-mock').exists()).toBe(false)
    })

    it('should display article title when provided', () => {
      const wrapper = mountComponent({
        open: true,
        title: 'Test Article Title',
      })
      expect(wrapper.text()).toContain('Test Article Title')
    })

    it('should display URL as title when title not provided', () => {
      const wrapper = mountComponent({
        open: true,
        url: 'https://example.com/article',
      })
      expect(wrapper.text()).toContain('example.com')
    })
  })

  describe('content fetching', () => {
    it('should show loading indicator', async () => {
      const wrapper = mountComponent()
      const loadingElements = wrapper.findAll('.animate-spin')
      expect(loadingElements.length > 0 || wrapper.text().includes('Loading')).toBe(true)
    })
  })

  describe('actions', () => {
    it('should emit update:open when close button clicked', async () => {
      const wrapper = mountComponent({ open: true })

      const closeButton = wrapper.find('.close-btn')
      await closeButton.trigger('click')

      expect(wrapper.emitted('update:open')).toBeTruthy()
      expect(wrapper.emitted('update:open')![0]).toEqual([false])
    })

    it('should have open in new tab button with correct link', async () => {
      const wrapper = mountComponent({
        open: true,
        url: 'https://example.com/article',
      })

      const link = wrapper.find('a[target="_blank"]')
      expect(link.exists()).toBe(true)
      expect(link.attributes('href')).toBe('https://example.com/article')
    })
  })

  describe('accessibility', () => {
    it('should have close button with title attribute', async () => {
      const wrapper = mountComponent({ open: true })

      const closeButton = wrapper.find('.close-btn')
      expect(closeButton.attributes('title')).toBeTruthy()
    })
  })
})