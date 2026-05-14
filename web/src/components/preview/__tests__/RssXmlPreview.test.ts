import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import RssXmlPreview from '../RssXmlPreview.vue'

// Mock DOMPurify
vi.mock('dompurify', () => ({
  default: {
    sanitize: (html: string) => html,
  },
}))

describe('RssXmlPreview', () => {
  it('renders XML content with syntax highlighting', () => {
    const wrapper = mount(RssXmlPreview, {
      props: { content: '<rss version="2.0"><channel>Test</channel></rss>' }
    })
    expect(wrapper.find('.code-content').exists()).toBe(true)
    expect(wrapper.html()).toContain('xml-tag-name')
    expect(wrapper.html()).toContain('rss')
  })

  it('renders with line numbers', () => {
    const wrapper = mount(RssXmlPreview, {
      props: { content: '<rss></rss>' }
    })
    expect(wrapper.html()).toContain('code-line-number')
  })

  it('handles quoted content (removes outer quotes)', () => {
    const wrapper = mount(RssXmlPreview, {
      props: { content: '"<rss></rss>"' }
    })
    // The cleaned content should NOT have outer quotes in the output
    expect(wrapper.html()).not.toContain('&quot;')
  })

  it('handles empty content', () => {
    const wrapper = mount(RssXmlPreview, {
      props: { content: '' }
    })
    expect(wrapper.find('.code-content').exists()).toBe(true)
  })
})
