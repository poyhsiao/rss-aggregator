import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import JsonPreview from '../JsonPreview.vue'

// Mock DOMPurify
vi.mock('dompurify', () => ({
  default: {
    sanitize: (html: string) => html,
  },
}))

describe('JsonPreview', () => {
  it('renders JSON content with syntax highlighting', () => {
    const wrapper = mount(JsonPreview, {
      props: { content: [{ key: 'value' }] }
    })
    expect(wrapper.find('.code-content').exists()).toBe(true)
    expect(wrapper.html()).toContain('hljs-attr')
  })

  it('renders with line numbers', () => {
    const wrapper = mount(JsonPreview, {
      props: { content: [{ a: 1 }] }
    })
    expect(wrapper.html()).toContain('code-line-number')
  })

  it('handles null content', () => {
    const wrapper = mount(JsonPreview, {
      props: { content: null }
    })
    expect(wrapper.find('.code-content').exists()).toBe(true)
  })
})
