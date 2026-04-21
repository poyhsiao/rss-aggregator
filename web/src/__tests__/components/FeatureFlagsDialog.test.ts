import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { setActivePinia, createPinia } from 'pinia'
import { useFeatureFlagsStore } from '@/stores/featureFlags'

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: {
    en: {
      featureFlags: {
        title: 'Feature Flags',
        groups: 'Group Settings',
        schedules: 'Scheduled Updates',
        shareLinks: 'Share Links',
      },
    },
    zh: {
      featureFlags: {
        title: '功能開關',
        groups: '群組設定功能',
        schedules: '定時更新功能',
        shareLinks: '分享連結功能',
      },
    },
  },
})

const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key]
    }),
    clear: vi.fn(() => {
      store = {}
    }),
  }
})()

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

vi.mock('@/api', () => ({
  default: {
    get: vi.fn(),
    patch: vi.fn(),
  },
}))

describe('FeatureFlagsDialog', () => {
  beforeEach(async () => {
    setActivePinia(createPinia())
    localStorageMock.clear()
    vi.clearAllMocks()
  })

  const mountComponent = async (props = { open: true }) => {
    const { default: FeatureFlagsDialog } = await import('../../components/FeatureFlagsDialog.vue')
    return mount(FeatureFlagsDialog, {
      props,
      global: {
        plugins: [i18n],
        stubs: {
          Dialog: {
            template: '<div class="dialog-stub" v-if="open"><slot /></div>',
            props: ['open', 'size'],
          },
        },
      },
    })
  }

  describe('rendering', () => {
    it('should render dialog when open', async () => {
      const wrapper = await mountComponent({ open: true })
      expect(wrapper.find('.dialog-stub').exists()).toBe(true)
    })

    it('should not render dialog when closed', async () => {
      const wrapper = await mountComponent({ open: false })
      expect(wrapper.find('.dialog-stub').exists()).toBe(false)
    })
  })

  describe('close button', () => {
    it('should emit update:open when close button clicked', async () => {
      const wrapper = await mountComponent({ open: true })
      const closeButton = wrapper.find('.close-btn')
      await closeButton.trigger('click')
      expect(wrapper.emitted('update:open')).toBeTruthy()
      expect(wrapper.emitted('update:open')![0]).toEqual([false])
    })
  })

  describe('feature toggles', () => {
    it('should display three feature toggle switches', async () => {
      const wrapper = await mountComponent({ open: true })
      const toggles = wrapper.findAll('.toggle-switch')
      expect(toggles).toHaveLength(3)
    })

    it('should display groups toggle with correct label', async () => {
      const wrapper = await mountComponent({ open: true })
      const label = wrapper.find('.label-groups')
      expect(label.text()).toContain('Group Settings')
    })

    it('should display schedules toggle with correct label', async () => {
      const wrapper = await mountComponent({ open: true })
      const label = wrapper.find('.label-schedules')
      expect(label.text()).toContain('Scheduled Updates')
    })

    it('should display shareLinks toggle with correct label', async () => {
      const wrapper = await mountComponent({ open: true })
      const label = wrapper.find('.label-shareLinks')
      expect(label.text()).toContain('Share Links')
    })
  })

  describe('toggle behavior', () => {
    it('should call store.toggle when groups switch is clicked', async () => {
      const wrapper = await mountComponent({ open: true })
      const toggle = wrapper.find('.toggle-groups')
      await toggle.trigger('click')
    })

    it('should call store.toggle when schedules switch is clicked', async () => {
      const wrapper = await mountComponent({ open: true })
      const toggle = wrapper.find('.toggle-schedules')
      await toggle.trigger('click')
    })

    it('should call store.toggle when shareLinks switch is clicked', async () => {
      const wrapper = await mountComponent({ open: true })
      const toggle = wrapper.find('.toggle-shareLinks')
      await toggle.trigger('click')
    })
  })

  describe('cascade logic: groups → schedules', () => {
    it('should disable schedules toggle when groups is OFF', async () => {
      const wrapper = await mountComponent({ open: true })
      const schedulesBtn = wrapper.find('.toggle-schedules')
      expect(schedulesBtn.attributes('disabled')).toBeDefined()
      expect(schedulesBtn.attributes('aria-disabled')).toBeDefined()
    })

    it('should NOT call store.toggle for schedules when groups is OFF', async () => {
      const store = useFeatureFlagsStore()
      store.feature_groups = false
      store.feature_schedules = true
      const toggleSpy = vi.spyOn(store, 'toggle')
      const wrapper = await mountComponent({ open: true })
      const schedulesToggle = wrapper.find('.toggle-schedules')
      await schedulesToggle.trigger('click')
      expect(toggleSpy).not.toHaveBeenCalled()
    })

    it('should cascade-disable schedules when groups is toggled OFF', async () => {
      const store = useFeatureFlagsStore()
      store.feature_groups = true
      store.feature_schedules = true
      const wrapper = await mountComponent({ open: true })
      expect(store.feature_schedules).toBe(true)
      const groupsToggle = wrapper.find('.toggle-groups')
      await groupsToggle.trigger('click')
      await flushPromises()
      expect(store.feature_groups).toBe(false)
      expect(store.feature_schedules).toBe(false)
    })

    it('should show schedules toggle as visually disabled when groups is OFF', async () => {
      const store = useFeatureFlagsStore()
      store.feature_groups = false
      store.feature_schedules = true
      const wrapper = await mountComponent({ open: true })
      const schedulesToggle = wrapper.find('.toggle-schedules')
      expect(schedulesToggle.classes()).toContain('opacity-50')
      expect(schedulesToggle.classes()).toContain('cursor-not-allowed')
    })
  })
})
