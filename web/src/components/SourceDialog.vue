<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { z } from 'zod'
import { X, Check } from 'lucide-vue-next'
import Dialog from '@/components/ui/Dialog.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Select from '@/components/ui/Select.vue'
import { createSource, updateSource } from '@/api/sources'
import { useToast } from '@/composables/useToast'
import type { Source } from '@/types/source'

const { t } = useI18n()
const toast = useToast()

const props = defineProps<{
  open: boolean
  source?: Source | null
}>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'saved'): void
}>()

const isEditMode = computed(() => !!props.source)

const schema = z.object({
  name: z.string().min(1, t('sources.name_required')),
  url: z.string().url(t('sources.url_invalid')),
  fetch_interval: z.number().min(0).max(604800).default(0),
  is_active: z.boolean().default(true),
})

type FormData = z.infer<typeof schema>

const form = ref<FormData>({
  name: '',
  url: '',
  fetch_interval: 0,
  is_active: true,
})

const fetchIntervalStr = computed({
  get: () => String(form.value.fetch_interval),
  set: (val: string) => { form.value.fetch_interval = Number(val) }
})

const errors = ref<Partial<Record<keyof FormData, string>>>({})
const loading = ref(false)

const intervalOptions = computed(() => [
  { value: '0', label: t('sources.interval_never') },
  { value: '3600', label: t('sources.interval_1h') },
  { value: '10800', label: t('sources.interval_3h') },
  { value: '21600', label: t('sources.interval_6h') },
  { value: '43200', label: t('sources.interval_12h') },
  { value: '86400', label: t('sources.interval_24h') },
  { value: '259200', label: t('sources.interval_3d') },
  { value: '604800', label: t('sources.interval_7d') },
])

watch(() => props.open, (open) => {
  if (open) {
    reset()
    if (props.source) {
      form.value = {
        name: props.source.name,
        url: props.source.url,
        fetch_interval: props.source.fetch_interval,
        is_active: props.source.is_active,
      }
    }
  }
})

function reset(): void {
  form.value = {
    name: '',
    url: '',
    fetch_interval: 0,
    is_active: true,
  }
  errors.value = {}
}

function close(): void {
  emit('update:open', false)
}

function validate(): boolean {
  const result = schema.safeParse(form.value)
  if (result.success) {
    errors.value = {}
    return true
  }
  
  errors.value = {}
  for (const issue of result.error.issues) {
    const field = issue.path[0] as keyof FormData
    errors.value[field] = issue.message
  }
  return false
}

async function handleSubmit(): Promise<void> {
  if (!validate()) return
  
  loading.value = true
  try {
    if (isEditMode.value && props.source) {
      await updateSource(props.source.id, form.value)
      toast.success(t('sources.updated'))
    } else {
      await createSource(form.value)
      toast.success(t('sources.created'))
    }
    emit('saved')
    close()
  } catch {
    toast.error(t('common.error'))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <div class="p-6">
      <h2 class="text-xl font-semibold mb-4">
        {{ isEditMode ? t('sources.edit') : t('sources.add') }}
      </h2>
      
      <form class="space-y-4" @submit.prevent="handleSubmit">
        <div>
          <label class="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
            {{ t('sources.name') }} *
          </label>
          <Input
            v-model="form.name"
            :placeholder="t('sources.name_placeholder')"
          />
          <p v-if="errors.name" class="text-red-500 text-sm mt-1">
            {{ errors.name }}
          </p>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
            {{ t('sources.url') }} *
          </label>
          <Input
            v-model="form.url"
            type="url"
            :placeholder="t('sources.url_placeholder')"
          />
          <p v-if="errors.url" class="text-red-500 text-sm mt-1">
            {{ errors.url }}
          </p>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
            {{ t('sources.fetch_interval') }}
          </label>
          <Select
            v-model="fetchIntervalStr"
            :options="intervalOptions"
          />
        </div>
        
        <div class="flex items-center gap-2">
          <input
            v-model="form.is_active"
            type="checkbox"
            class="rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
          />
          <label class="text-sm text-neutral-700 dark:text-neutral-300">
            {{ t('sources.active') }}
          </label>
        </div>
        
        <div class="flex justify-end gap-2 pt-4">
          <Button type="button" variant="outline" @click="close" :title="t('common.cancel')">
            <X class="h-4 w-4" />
            {{ t('common.cancel') }}
          </Button>
          <Button type="submit" :disabled="loading" :title="t('common.confirm')">
            <Check class="h-4 w-4" />
            {{ loading ? t('common.loading') : t('common.confirm') }}
          </Button>
        </div>
      </form>
    </div>
  </Dialog>
</template>