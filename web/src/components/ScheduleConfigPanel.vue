<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Clock, Plus, Pencil, Trash2, Power, PowerOff } from 'lucide-vue-next'
import { getSchedules, createSchedule, deleteSchedule, toggleSchedule } from '@/api/schedules'
import type { Schedule } from '@/types/schedule'
import Button from '@/components/ui/Button.vue'
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'

const { t } = useI18n()
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

const minuteOptions = Array.from({ length: 60 }, (_, i) => i)
const hourOptions = Array.from({ length: 24 }, (_, i) => i)
const weekdayOptions = [
  { value: 0, label: 'schedule.weekdays_options.0' },
  { value: 1, label: 'schedule.weekdays_options.1' },
  { value: 2, label: 'schedule.weekdays_options.2' },
  { value: 3, label: 'schedule.weekdays_options.3' },
  { value: 4, label: 'schedule.weekdays_options.4' },
  { value: 5, label: 'schedule.weekdays_options.5' },
  { value: 6, label: 'schedule.weekdays_options.6' },
]

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
    parts.push(timeParts.join(', '))
  } else if (hours.length) {
    parts.push(hours.map(h => `${h}:00`).join(', '))
  } else if (mins.length) {
    parts.push(`:${mins.join(', ')}`)
  }

  return parts.join(' ')
})

function buildDetailedCron(): string {
  const mins = selectedMinutes.value.join(',') || '*'
  const hours = selectedHours.value.join(',') || '*'
  const days = selectedWeekdays.value.join(',') || '*'
  return `${mins} ${hours} * * ${days}`
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
  if (!at) return '—'
  const date = new Date(at)
  return date.toLocaleString('zh-TW', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

onMounted(fetchSchedules)
</script>

<template>
  <div class="mt-4 pt-4 border-t border-neutral-100 dark:border-neutral-700">
    <div class="flex items-center gap-2 mb-4">
      <Clock class="h-4 w-4 text-blue-500" />
      <span class="font-medium">{{ t('schedule.title') }}</span>
    </div>

    <div class="mb-4">
      <label class="flex items-center gap-4 text-sm">
        <input type="radio" v-model="mode" value="quick" :checked="mode === 'quick'" />
        {{ t('schedule.quick') }}
        <input type="radio" v-model="mode" value="detailed" :checked="mode === 'detailed'" />
        {{ t('schedule.detailed') }}
      </label>
    </div>

    <div v-if="mode === 'quick'" class="mb-4">
      <select v-model="quickCron" class="w-full px-3 py-2 rounded-lg border border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-800">
        <option v-for="opt in quickOptions" :key="opt.value" :value="opt.value">
          {{ t(opt.label) }}
        </option>
      </select>
    </div>

    <div v-else class="space-y-3 mb-4">
      <div>
        <div class="text-sm font-medium mb-1">{{ t('schedule.minutes') }}</div>
        <div class="flex flex-wrap gap-1">
          <button
            v-for="m in minuteOptions"
            :key="m"
            type="button"
            :class="selectedMinutes.includes(m) ? 'bg-blue-500 text-white' : 'bg-neutral-100 dark:bg-neutral-700'"
            class="w-8 h-6 text-xs rounded"
            @click="selectedMinutes.includes(m) ? selectedMinutes = selectedMinutes.filter(x => x !== m) : selectedMinutes.push(m)"
          >
            {{ m }}
          </button>
        </div>
      </div>
      <div>
        <div class="text-sm font-medium mb-1">{{ t('schedule.hours') }}</div>
        <div class="flex flex-wrap gap-1">
          <button
            v-for="h in hourOptions"
            :key="h"
            type="button"
            :class="selectedHours.includes(h) ? 'bg-blue-500 text-white' : 'bg-neutral-100 dark:bg-neutral-700'"
            class="w-8 h-6 text-xs rounded"
            @click="selectedHours.includes(h) ? selectedHours = selectedHours.filter(x => x !== h) : selectedHours.push(h)"
          >
            {{ h }}
          </button>
        </div>
      </div>
      <div>
        <div class="text-sm font-medium mb-1">{{ t('schedule.weekdays') }}</div>
        <div class="flex flex-wrap gap-1">
          <button
            v-for="d in weekdayOptions"
            :key="d.value"
            type="button"
            :class="selectedWeekdays.includes(d.value) ? 'bg-blue-500 text-white' : 'bg-neutral-100 dark:bg-neutral-700'"
            class="w-10 h-6 text-xs rounded"
            @click="selectedWeekdays.includes(d.value) ? selectedWeekdays = selectedWeekdays.filter(x => x !== d.value) : selectedWeekdays.push(d.value)"
          >
            {{ t(d.label) }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="cronPreview" class="mb-4 text-sm text-neutral-500 dark:text-neutral-400">
      {{ t('schedule.preview') }}: {{ cronPreview }}
    </div>

    <div class="flex gap-2 mb-4">
      <Button @click="handleSave" :disabled="saving">
        <Plus class="h-4 w-4 mr-1" /> {{ t('schedule.add') }}
      </Button>
    </div>

    <div v-if="loading" class="text-center py-4 text-neutral-500">
      {{ t('common.loading') }}
    </div>

    <div v-else-if="!schedules.length" class="text-center py-4 text-neutral-500">
      {{ t('schedule.empty') }}
    </div>

    <div v-else class="space-y-2">
      <div
        v-for="s in schedules"
        :key="s.id"
        class="flex items-center justify-between p-3 bg-neutral-50 dark:bg-neutral-900 rounded-lg"
      >
        <div class="flex items-center gap-2">
          <Clock class="h-4 w-4" :class="s.is_enabled ? 'text-green-500' : 'text-neutral-400'" />
          <span class="text-sm">{{ s.cron_expression }}</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-xs text-neutral-500">{{ s.next_run_at ? formatNextRun(s.next_run_at) : t('schedule.disabled') }}</span>
          <Button variant="ghost" size="sm" @click="handleToggle(s.id)">
            <Power v-if="s.is_enabled" class="h-4 w-4 text-green-500" />
            <PowerOff v-else class="h-4 w-4 text-neutral-400" />
          </Button>
          <Button variant="ghost" size="sm" @click="handleDelete(s.id)">
            <Trash2 class="h-4 w-4 text-red-500" />
          </Button>
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