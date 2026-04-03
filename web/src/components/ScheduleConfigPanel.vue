<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Clock, Plus, Trash2, Power, PowerOff } from 'lucide-vue-next'
import cronstrue from 'cronstrue/i18n'
import { getSchedules, createSchedule, deleteSchedule, toggleSchedule } from '@/api/schedules'
import type { Schedule } from '@/types/schedule'
import Button from '@/components/ui/Button.vue'
import MultiSelect from '@/components/ui/MultiSelect.vue'
import TooltipButton from '@/components/ui/TooltipButton.vue'
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'

const { t, locale } = useI18n()
const toast = useToast()
const confirm = useConfirm()

const props = defineProps<{
  groupId: number
}>()

const emit = defineEmits<{
  saved: []
}>()

type ScheduleMode = 'quick' | 'detailed'

const schedules = ref<Schedule[]>([])
const loading = ref(true)
const mode = ref<ScheduleMode>('quick')
const quickCron = ref('*/15 * * * *')
const saving = ref(false)

const selectedMinutes = ref<number[]>([])
const selectedHours = ref<number[]>([])
const selectedWeekdays = ref<number[]>([])

const quickOptions = [
  { label: 'schedule.quick_options.every_15min', value: '*/15 * * * *' },
  { label: 'schedule.quick_options.every_30min', value: '*/30 * * * *' },
  { label: 'schedule.quick_options.every_1hour', value: '0 * * * *' },
  { label: 'schedule.quick_options.every_3hours', value: '0 */3 * * *' },
  { label: 'schedule.quick_options.every_6hours', value: '0 */6 * * *' },
  { label: 'schedule.quick_options.every_12hours', value: '0 */12 * * *' },
  { label: 'schedule.quick_options.daily', value: '30 8 * * *' },
]

const weekdayOptions = computed(() => [
  { value: 0, label: t('schedule.weekdays_options.0') },
  { value: 1, label: t('schedule.weekdays_options.1') },
  { value: 2, label: t('schedule.weekdays_options.2') },
  { value: 3, label: t('schedule.weekdays_options.3') },
  { value: 4, label: t('schedule.weekdays_options.4') },
  { value: 5, label: t('schedule.weekdays_options.5') },
  { value: 6, label: t('schedule.weekdays_options.6') },
])

const minuteOptions = Array.from({ length: 60 }, (_, i) => ({ value: i, label: i.toString().padStart(2, '0') }))
const hourOptions = Array.from({ length: 24 }, (_, i) => ({ value: i, label: `${i.toString().padStart(2, '0')}:00` }))

const cronPreview = computed(() => {
  if (mode.value === 'quick') {
    const opt = quickOptions.find(o => o.value === quickCron.value)
    return opt ? t(opt.label) : ''
  }

  const mins = selectedMinutes.value.sort((a, b) => a - b)
  const hours = selectedHours.value.sort((a, b) => a - b)
  const days = selectedWeekdays.value.sort((a, b) => a - b)

  if (!mins.length && !hours.length && !days.length) return ''

  const parts: string[] = []

  if (days.length) {
    const dayNames = days.map(d => t(`schedule.weekdays_options.${d}`)).join(', ')
    parts.push(dayNames)
  }

  if (mins.length && hours.length) {
    const timeParts = hours.flatMap(h => mins.map(m => `${h}:${m.toString().padStart(2, '0')}`))
    if (timeParts.length > 8) {
      parts.push(`${timeParts.slice(0, 8).join(', ')}... (+${timeParts.length - 8})`)
    } else {
      parts.push(timeParts.join(', '))
    }
  } else if (hours.length) {
    parts.push(hours.map(h => `${h}:00`).join(', '))
  } else if (mins.length) {
    if (mins.length > 12) {
      parts.push(`:${mins.slice(0, 12).join(', ')}... (+${mins.length - 12})`)
    } else {
      parts.push(`:${mins.join(', ')}`)
    }
  }

  return parts.join(' ')
})

function buildDetailedCron(): string {
  const mins = selectedMinutes.value.join(',') || '*'
  const hours = selectedHours.value.join(',') || '*'
  const days = selectedWeekdays.value.join(',') || '*'
  return `${mins} ${hours} * * ${days}`
}

function formatCronHumanReadable(cronExpression: string): string {
  try {
    const lang = locale.value.startsWith('zh') ? 'zh_TW' : 'en'
    return cronstrue.toString(cronExpression, { locale: lang })
  } catch {
    return cronExpression
  }
}

async function fetchSchedules() {
  loading.value = true
  try {
    schedules.value = await getSchedules(props.groupId)
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  if (schedules.value.length >= 10) {
    toast.error(t('schedule.max_reached'))
    return
  }

  const cron = mode.value === 'quick' ? quickCron.value : buildDetailedCron()
  saving.value = true
  try {
    await createSchedule(props.groupId, { cron_expression: cron })
    toast.success(t('common.success'))
    await fetchSchedules()
    emit('saved')
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    const msg = err.response?.data?.detail || t('common.error')
    toast.error(msg)
  } finally {
    saving.value = false
  }
}

async function handleToggle(id: number) {
  try {
    await toggleSchedule(props.groupId, id)
    await fetchSchedules()
    toast.success(t('common.success'))
  } catch {
    toast.error(t('common.error'))
  }
}

async function handleDelete(id: number) {
  const confirmed = await confirm.show({
    title: t('schedule.delete_title'),
    message: t('schedule.delete_confirm'),
    confirmText: t('common.delete'),
    cancelText: t('common.cancel'),
    variant: 'danger'
  })
  if (!confirmed) return

  try {
    await deleteSchedule(props.groupId, id)
    await fetchSchedules()
    toast.success(t('common.success'))
  } catch {
    toast.error(t('common.error'))
  }
}

function formatNextRun(at: string | null): string {
  if (!at) return t('schedule.disabled')
  const date = new Date(at)
  return date.toLocaleString('zh-TW', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

onMounted(fetchSchedules)
</script>

<template>
  <div>
    <!-- Section Header -->
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2">
        <Clock class="h-4 w-4 text-blue-500" />
        <span class="font-medium text-sm">{{ t('schedule.title') }}</span>
      </div>
      <TooltipButton :text="t('schedule.help_text')" />
    </div>

    <!-- Mode Selection -->
    <div class="flex gap-3 mb-3">
      <label class="flex items-center gap-1.5 cursor-pointer text-sm">
        <input type="radio" v-model="mode" value="quick" class="accent-blue-500" />
        {{ t('schedule.quick') }}
      </label>
      <label class="flex items-center gap-1.5 cursor-pointer text-sm">
        <input type="radio" v-model="mode" value="detailed" class="accent-blue-500" />
        {{ t('schedule.detailed') }}
      </label>
    </div>

    <!-- Quick Mode -->
    <div v-if="mode === 'quick'" class="mb-3">
      <select v-model="quickCron" class="w-full px-3 py-2.5 text-sm rounded-xl border border-neutral-200 bg-white dark:border-neutral-700 dark:bg-neutral-800 min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary-500">
        <option v-for="opt in quickOptions" :key="opt.value" :value="opt.value">
          {{ t(opt.label) }}
        </option>
      </select>
    </div>

    <!-- Detailed Mode - MultiSelect Dropdowns -->
    <div v-else class="space-y-3 mb-3">
      <!-- Weekday Multi-Select -->
      <div>
        <label class="block text-xs font-medium text-neutral-600 dark:text-neutral-400 mb-1.5">{{ t('schedule.weekdays') }}</label>
        <MultiSelect
          v-model="selectedWeekdays"
          :options="weekdayOptions"
          :placeholder="t('schedule.weekdays')"
          :max-display="4"
        />
      </div>

      <!-- Hour Multi-Select -->
      <div>
        <label class="block text-xs font-medium text-neutral-600 dark:text-neutral-400 mb-1.5">{{ t('schedule.hours') }}</label>
        <MultiSelect
          v-model="selectedHours"
          :options="hourOptions"
          :placeholder="t('schedule.hours')"
          :max-display="4"
        />
      </div>

      <!-- Minute Multi-Select -->
      <div>
        <label class="block text-xs font-medium text-neutral-600 dark:text-neutral-400 mb-1.5">{{ t('schedule.minutes') }}</label>
        <MultiSelect
          v-model="selectedMinutes"
          :options="minuteOptions"
          :placeholder="t('schedule.minutes')"
          :max-display="6"
        />
      </div>
    </div>

    <!-- Cron Preview -->
    <div v-if="cronPreview" class="mb-3 px-3 py-2.5 bg-blue-50 dark:bg-blue-950/30 rounded-lg">
      <div class="text-xs text-blue-600 dark:text-blue-400 font-medium">{{ t('schedule.preview') }}</div>
      <div class="text-sm text-blue-800 dark:text-blue-300">{{ cronPreview }}</div>
    </div>

    <!-- Add Button -->
    <Button @click="handleSave" :disabled="saving" class="w-full text-sm min-h-[44px]">
      <Plus class="h-4 w-4 mr-1" /> {{ t('schedule.add') }}
    </Button>

    <!-- Schedule List -->
    <div v-if="loading" class="text-center py-4 text-neutral-500 text-sm">
      {{ t('common.loading') }}
    </div>

    <div v-else-if="!schedules.length" class="text-center py-4 text-neutral-500 text-sm">
      {{ t('schedule.empty') }}
    </div>

    <div v-else class="space-y-2 mt-3">
      <div
        v-for="s in schedules"
        :key="s.id"
        class="flex flex-col sm:flex-row sm:items-center justify-between p-3 bg-neutral-50 dark:bg-neutral-900 rounded-lg gap-2"
      >
        <div class="flex items-center gap-2 min-w-0 flex-1">
          <Clock class="h-4 w-4 shrink-0" :class="s.is_enabled ? 'text-green-500' : 'text-neutral-400'" />
          <div class="min-w-0 flex-1">
            <div class="text-sm font-medium truncate">{{ formatCronHumanReadable(s.cron_expression) }}</div>
            <div class="text-xs text-neutral-500 dark:text-neutral-400 font-mono">{{ s.cron_expression }}</div>
          </div>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <span class="text-xs text-neutral-500">{{ t('schedule.next_run') }}: {{ formatNextRun(s.next_run_at) }}</span>
          <button
            type="button"
            :class="s.is_enabled ? 'text-green-500 hover:text-green-600' : 'text-neutral-400 hover:text-neutral-500'"
            :title="s.is_enabled ? t('schedule.disable') : t('schedule.enable')"
            class="p-2 min-w-[40px] min-h-[40px] flex items-center justify-center rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-700"
            @click="handleToggle(s.id)"
          >
            <Power v-if="s.is_enabled" class="h-4 w-4" />
            <PowerOff v-else class="h-4 w-4" />
          </button>
          <button
            type="button"
            :title="t('schedule.delete')"
            class="p-2 min-w-[40px] min-h-[40px] flex items-center justify-center rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-700 text-red-500 hover:text-red-600"
            @click="handleDelete(s.id)"
          >
            <Trash2 class="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>

    <ConfirmDialog
      v-model:open="confirm.state.value.open"
      :title="confirm.state.value.title"
      :message="confirm.state.value.message"
      :confirm-text="confirm.state.value.confirmText"
      :cancel-text="confirm.state.value.cancelText"
      :variant="confirm.state.value.variant"
      @confirm="confirm.confirm"
      @cancel="confirm.cancel"
    />
  </div>
</template>
