import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { ref } from 'vue'
import { createPinia, setActivePinia } from 'pinia'
import RssPreviewDialog from '../RssPreviewDialog.vue'
import Button from '@/components/ui/Button.vue'
import { useFeatureFlagsStore } from '@/stores/featureFlags'

vi.mock('@/api/app-settings', () => ({
  getAppSettings: vi.fn().mockResolvedValue({
    group_enabled: false,
    schedule_enabled: false,
    share_enabled: true,
    source_group_schedules_enabled: false,
  }),
  updateAppSettings: vi.fn().mockResolvedValue({
    group_enabled: false,
    schedule_enabled: false,
    share_enabled: true,
    source_group_schedules_enabled: false,
  }),
}))

vi.mock('@/composables/useFeedCache', () => ({
  useFeedCache: () => ({
    rssContent: ref('<rss></rss>'),
    jsonContent: ref([]),
    markdownContent: ref('# Markdown'),
    loading: ref(false),
    error: ref(null),
    fetchRssContent: vi.fn(),
    fetchContentForFormat: vi.fn(),
    resetCache: vi.fn(),
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
      feed: {
        format_rss: 'RSS',
        format_json: 'JSON',
        format_markdown: 'Markdown',
        share_links: 'Share Links',
        download: 'Download',
        copy: 'Copy',
        copied: 'Copied!',
        item: 'item',
        items: 'items',
        preview_title: 'Preview',
        preview_source_title: 'Source Preview',
        copy_path: 'Copy path',
      },
      keys: {
        copy: 'Copy',
        copied: 'Copied!',
      },
    },
  },
})

describe('RssPreviewDialog', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    const store = useFeatureFlagsStore()
    store.shareEnabled = true
    vi.clearAllMocks()
  })

  const mountComponent = (props = {}) => {
    return mount(RssPreviewDialog, {
      props: {
        open: true,
        ...props,
      },
      global: {
        plugins: [i18n],
        components: { Button },
        stubs: {
          Dialog: {
            template: '<div class="dialog-mock" v-if="open"><slot /></div>',
            props: ['open', 'size'],
          },
          RssXmlPreview: { template: '<div class="rss-preview-mock" />' },
          JsonPreview: { template: '<div class="json-preview-mock" />' },
          MarkdownPreview: { template: '<div class="markdown-preview-mock" />' },
          Teleport: true,
        },
      },
    })
  }

  describe('Share Links button placement', () => {
    it('Share Links button is in the same row as Copy and Download buttons', async () => {
      const wrapper = mountComponent({
        open: true,
        params: { source_id: 1, format: 'rss' },
      })

      // Find the button row container
      const buttonRow = wrapper.find('div.flex.justify-end.gap-2')
      expect(buttonRow.exists()).toBe(true)

      // Get all buttons in the button row
      const buttonsInRow = buttonRow.findAll('button')

      // Should have 3 buttons: Copy, Download, and Share Links
      expect(buttonsInRow.length).toBe(3)

      // Verify all three buttons exist by text
      const buttonTexts = buttonsInRow.map(b => b.text().trim())
      expect(buttonTexts).toContain('Copy')
      expect(buttonTexts).toContain('Download')
      expect(buttonTexts).toContain('Share Links')
    })
  })
})
