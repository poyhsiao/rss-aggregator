import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import PreviewContainer from '../PreviewContainer.vue'

// Mock DOMPurify
vi.mock('dompurify', () => ({
  default: {
    sanitize: (html: string) => html,
  },
}))

describe('PreviewContainer', () => {
  it('renders content with v-html', () => {
    const wrapper = mount(PreviewContainer, {
      props: { content: '<span class="xml-tag-name">test</span>' }
    })
    expect(wrapper.find('.code-content').exists()).toBe(true)
    expect(wrapper.html()).toContain('test')
  })

  it('sanitizes dangerous content (no script tags)', () => {
    // Test with mock that actually sanitizes - mock returns empty string for script tags
    vi.mock('dompurify', () => ({
      default: {
        sanitize: (html: string) => html.replace(/<script>.*?<\/script>/gi, ''),
      },
    }))
    const wrapper = mount(PreviewContainer, {
      props: { content: '<script>alert(1)</script><span>safe</span>' }
    })
    expect(wrapper.html()).not.toContain('script')
    expect(wrapper.html()).toContain('safe')
  })

  it('allows additional tags when specified', () => {
    const wrapper = mount(PreviewContainer, {
      props: { content: '<div>test</div>', allowedTags: ['span', 'div'] }
    })
    expect(wrapper.html()).toContain('<div>test</div>')
  })

  it('returns empty for empty content', () => {
    const wrapper = mount(PreviewContainer, {
      props: { content: '' }
    })
    expect(wrapper.find('.code-content').text()).toBe('')
  })

  it('handles content with code-line-number spans', () => {
    const wrapper = mount(PreviewContainer, {
      props: { content: '<div class="code-line"><span class="code-line-number">1</span><span class="code-line-content">line1</span></div>' }
    })
    expect(wrapper.html()).toContain('code-line-number')
    expect(wrapper.html()).toContain('code-line-content')
  })
})
