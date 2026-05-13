import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import MarkdownPreview from '../MarkdownPreview.vue'

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: {
    en: { feed: { view_source: 'Source', view_preview: 'Preview' } }
  }
})

// Mock DOMPurify
vi.mock('dompurify', () => ({
  default: {
    sanitize: (html: string) => html,
  },
}))

describe('MarkdownPreview', () => {
  it('renders in preview mode by default', () => {
    const wrapper = mount(MarkdownPreview, {
      props: { content: '# Hello World' },
      global: { plugins: [i18n] }
    })
    // Default mode is preview (rendered HTML), not source
    expect(wrapper.find('.prose').exists()).toBe(true)
  })

  it('can switch to source mode', async () => {
    const wrapper = mount(MarkdownPreview, {
      props: { content: '# Hello' },
      global: { plugins: [i18n], stubs: { LucideIcon: true } }
    })
    const buttons = wrapper.findAll('button')
    await buttons[0].trigger('click')
    expect(wrapper.find('.code-content').exists()).toBe(true)
  })

  it('can switch back to preview mode', async () => {
    const wrapper = mount(MarkdownPreview, {
      props: { content: '# Hello' },
      global: { plugins: [i18n], stubs: { LucideIcon: true } }
    })
    const buttons = wrapper.findAll('button')
    await buttons[0].trigger('click')
    await buttons[1].trigger('click')
    expect(wrapper.find('.prose').exists()).toBe(true)
  })
})
