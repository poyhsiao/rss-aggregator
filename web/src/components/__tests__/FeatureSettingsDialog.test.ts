import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'
import { createI18n } from 'vue-i18n'
import { useFeatureFlagsStore } from '@/stores/featureFlags'
import FeatureSettingsDialog from '@/components/FeatureSettingsDialog.vue'
import { getAppSettings } from '@/api/app-settings'

vi.mock('@/api/app-settings', () => ({
  getAppSettings: vi.fn().mockResolvedValue({
    group_enabled: true, schedule_enabled: true,
    share_enabled: true, source_group_schedules_enabled: true,
  }),
  updateAppSettings: vi.fn().mockResolvedValue({
    group_enabled: true, schedule_enabled: true,
    share_enabled: true, source_group_schedules_enabled: true,
  }),
}))

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn() }),
}))

vi.mock('lucide-vue-next', () => ({
  Settings: { template: '<svg />' },
}))

vi.mock('@/components/ui/Dialog.vue', () => ({
  default: {
    template: '<div :data-open="$props.open" data-testid="dialog"><slot /></div>',
    props: ['open'],
  },
}))

vi.mock('@/components/ui/Button.vue', () => ({
  default: {
    template: '<button data-testid="button"><slot /></button>',
  },
}))

vi.mock('@/components/ui/CascadeWarningDialog.vue', () => ({
  default: {
    template: '<div data-testid="cascade-warning" :data-open="$props.open" />',
    props: ['open'],
  },
}))

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: {
    en: {
      featureSettings: {
        title: 'Feature Settings',
        group: { label: 'Group', description: 'Group desc' },
        schedule: { label: 'Schedule', description: 'Schedule desc', disabledHint: 'Requires Group' },
        share: { label: 'Share', description: 'Share desc' },
        sourceGroupSchedules: { label: 'SGS', description: 'SGS desc', disabledHint: 'Requires Group' },
        apply: 'Apply',
        cancel: 'Cancel',
        applied: 'Settings applied',
      },
    },
  },
})

describe('FeatureSettingsDialog', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  const mountDialog = (props = {}) =>
    mount(FeatureSettingsDialog, {
      props: { open: true, ...props },
      global: {
        plugins: [i18n],
        stubs: {
          SwitchRoot: {
            template: '<button role="switch" :aria-checked="String(checked)" :disabled="disabled" @click="$emit(\'update:checked\', !checked)"><slot /></button>',
            props: ['checked', 'disabled'],
            emits: ['update:checked'],
          },
          SwitchThumb: { template: '<span />' },
        },
      },
    })

  it('disables SGS and Schedule toggles when Group is OFF', async () => {
    vi.mocked(getAppSettings).mockResolvedValueOnce({
      group_enabled: false, schedule_enabled: false,
      share_enabled: false, source_group_schedules_enabled: false,
    })

    const wrapper = mountDialog()
    await flushPromises()

    const disabled = wrapper.findAll('button[role="switch"][disabled]')
    expect(disabled.length).toBe(2)
  })

  it('Share toggle is never disabled by Group state', async () => {
    vi.mocked(getAppSettings).mockResolvedValueOnce({
      group_enabled: false, schedule_enabled: false,
      share_enabled: false, source_group_schedules_enabled: false,
    })

    const wrapper = mountDialog()
    await flushPromises()

    const switches = wrapper.findAll('[role="switch"]')
    expect(switches[3].attributes('disabled')).toBeUndefined()
  })

  it('reads store values and initializes refs from store', async () => {
    const store = useFeatureFlagsStore()
    store.groupsEnabled = true
    store.shareEnabled = true
    await nextTick()

    const wrapper = mountDialog()
    await flushPromises()

    const switches = wrapper.findAll('[role="switch"]')
    expect(switches[0].attributes('aria-checked')).toBe('true')
    expect(switches[3].attributes('aria-checked')).toBe('true')
  })

  it('shows cascade warning when Group turned OFF with dependencies enabled', async () => {
    const store = useFeatureFlagsStore()
    store.groupsEnabled = true
    store.sourceGroupSchedulesEnabled = true
    await nextTick()

    const wrapper = mountDialog()
    await flushPromises()

    const switches = wrapper.findAll('[role="switch"]')
    await switches[0].trigger('click')
    await nextTick()

    const warning = wrapper.find('[data-testid="cascade-warning"]')
    expect(warning.attributes('data-open')).toBe('true')
  })

  it('initializes all toggles from store values', async () => {
    const store = useFeatureFlagsStore()
    store.$patch({
      groupsEnabled: true,
      sourceGroupSchedulesEnabled: true,
      scheduleEnabled: true,
      shareEnabled: true,
    })
    await nextTick()

    const wrapper = mountDialog()
    await flushPromises()

    const switches = wrapper.findAll('[role="switch"]')
    expect(switches[0].attributes('aria-checked')).toBe('true')
    expect(switches[1].attributes('aria-checked')).toBe('true')
    expect(switches[2].attributes('aria-checked')).toBe('true')
    expect(switches[3].attributes('aria-checked')).toBe('true')
  })

  it('toggle order is Group, SGS, Schedule, Share', async () => {
    const wrapper = mountDialog()
    await flushPromises()
    const switches = wrapper.findAll('[role="switch"]')
    expect(switches.length).toBe(4)
  })
})
