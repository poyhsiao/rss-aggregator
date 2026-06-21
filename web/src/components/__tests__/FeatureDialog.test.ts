import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import FeatureDialog from '../FeatureDialog.vue'
import { useFeedUrlSettingsStore } from '@/stores/feedUrlSettings'

// Mock the store
vi.mock('@/stores/feedUrlSettings', () => ({
  useFeedUrlSettingsStore: vi.fn(() => ({
    enabled: false,
    fetchSettings: vi.fn(),
    setEnabled: vi.fn(),
  })),
}))

describe('FeatureDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const mountComponent = (props = {}) => {
    return mount(FeatureDialog, {
      props: {
        open: true,
        ...props,
      },
      global: {
        stubs: {
          Dialog: {
            template: '<div class="dialog-mock" v-if="open" data-testid="feature-dialog"><slot /></div>',
            props: ['open', 'size'],
          },
          Teleport: true,
        },
      },
    })
  }

  it('is not visible when open is false', () => {
    const wrapper = mountComponent({ open: false })
    expect(wrapper.find('.dialog-mock').exists()).toBe(false)
  })

  it('is visible when open is true', () => {
    const wrapper = mountComponent({ open: true })
    expect(wrapper.find('.dialog-mock').isVisible()).toBe(true)
  })

  it('emits update:open when close button clicked', async () => {
    const wrapper = mountComponent({ open: true })
    await wrapper.find('[data-testid=close-btn]').trigger('click')
    expect(wrapper.emitted('update:open')).toBeTruthy()
    expect(wrapper.emitted('update:open')![0]).toEqual([false])
  })

  it('calls setEnabled when toggle is clicked', async () => {
    const setEnabledMock = vi.fn()
    vi.mocked(useFeedUrlSettingsStore).mockReturnValue({
      enabled: false,
      fetchSettings: vi.fn(),
      setEnabled: setEnabledMock,
    })

    const wrapper = mountComponent({ open: true })
    await wrapper.find('[data-testid=feature-toggle]').trigger('click')
    expect(setEnabledMock).toHaveBeenCalledWith(true)
  })
})
