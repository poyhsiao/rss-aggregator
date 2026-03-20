<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Copy, Check, X, AlertCircle } from 'lucide-vue-next'
import Dialog from '@/components/ui/Dialog.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import { createKey } from '@/api/keys'
import { useToast } from '@/composables/useToast'
import type { ApiKey } from '@/types/key'

const { t } = useI18n()
const toast = useToast()

defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'created', key: ApiKey): void
}>()

const MIN_KEY_LENGTH = 16
const MAX_KEY_LENGTH = 255
const KEY_PATTERN = /^[a-zA-Z0-9_-]+$/

const name = ref('')
const customKey = ref('')
const useCustomKey = ref(false)
const loading = ref(false)
const createdKey = ref<ApiKey | null>(null)
const copied = ref(false)

const showKeyDisplay = computed(() => createdKey.value !== null)

const keyError = computed(() => {
  if (!useCustomKey.value || !customKey.value) return null
  
  if (customKey.value.length < MIN_KEY_LENGTH) {
    return t('keys.key_too_short', { min: MIN_KEY_LENGTH })
  }
  if (customKey.value.length > MAX_KEY_LENGTH) {
    return t('keys.key_too_long', { max: MAX_KEY_LENGTH })
  }
  if (!KEY_PATTERN.test(customKey.value)) {
    return t('keys.key_invalid_chars')
  }
  return null
})

const canSubmit = computed(() => {
  if (!useCustomKey.value) return true
  return customKey.value.length > 0 && !keyError.value
})

watch(useCustomKey, (newVal) => {
  if (!newVal) {
    customKey.value = ''
  }
})

function reset(): void {
  name.value = ''
  customKey.value = ''
  useCustomKey.value = false
  createdKey.value = null
  copied.value = false
}

function close(): void {
  reset()
  emit('update:open', false)
}

async function handleSubmit(): Promise<void> {
  if (!canSubmit.value) return
  
  loading.value = true
  try {
    const payload: { name?: string; key?: string } = {}
    if (name.value) payload.name = name.value
    if (useCustomKey.value && customKey.value) payload.key = customKey.value
    
    const newKey = await createKey(Object.keys(payload).length > 0 ? payload : undefined)
    createdKey.value = newKey
    toast.success(t('keys.created'))
    emit('created', newKey)
  } catch (error: any) {
    const detail = error?.response?.data?.detail
    if (detail === 'Key already exists') {
      toast.error(t('keys.key_exists'))
    } else {
      toast.error(t('common.error'))
    }
  } finally {
    loading.value = false
  }
}

async function copyKey(): Promise<void> {
  if (!createdKey.value) return
  
  try {
    await navigator.clipboard.writeText(createdKey.value.key)
    copied.value = true
    toast.success(t('keys.copied'))
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch {
    toast.error(t('keys.copy_failed'))
  }
}
</script>

<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <div class="p-6">
      <h2 class="text-xl font-semibold mb-4">
        {{ showKeyDisplay ? t('keys.key_created') : t('keys.add') }}
      </h2>
      
      <template v-if="!showKeyDisplay">
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
              {{ t('keys.name_optional') }}
            </label>
            <Input
              v-model="name"
              :placeholder="t('keys.name_placeholder')"
            />
          </div>
          
          <div class="border-t border-neutral-200 dark:border-neutral-700 pt-4">
            <label class="flex items-center gap-2 cursor-pointer">
              <input
                v-model="useCustomKey"
                type="checkbox"
                class="w-4 h-4 rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
              />
              <span class="text-sm font-medium text-neutral-700 dark:text-neutral-300">
                {{ t('keys.use_custom_key') }}
              </span>
            </label>
            
            <div v-if="useCustomKey" class="mt-3 space-y-2">
              <Input
                v-model="customKey"
                :placeholder="t('keys.custom_key_placeholder')"
                :class="{ 'border-red-500 dark:border-red-500': keyError }"
              />
              
              <div v-if="keyError" class="flex items-center gap-1 text-sm text-red-500">
                <AlertCircle class="h-4 w-4" />
                {{ keyError }}
              </div>
              
              <p class="text-xs text-neutral-500 dark:text-neutral-400">
                {{ t('keys.key_requirements', { min: MIN_KEY_LENGTH, max: MAX_KEY_LENGTH }) }}
              </p>
            </div>
          </div>
          
          <div class="flex justify-end gap-2 pt-4">
            <Button variant="outline" @click="close" :title="t('common.cancel')">
              <X class="h-4 w-4 mr-2" />
              {{ t('common.cancel') }}
            </Button>
            <Button :disabled="loading || !canSubmit" @click="handleSubmit" :title="t('common.confirm')">
              <Check class="h-4 w-4 mr-2" />
              {{ loading ? t('common.loading') : t('common.confirm') }}
            </Button>
          </div>
        </div>
      </template>
      
      <template v-else>
        <div class="space-y-4">
          <div class="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl">
            <p class="text-sm text-green-700 dark:text-green-300 mb-2">
              {{ t('keys.save_warning') }}
            </p>
            <div class="flex items-center gap-2">
              <code class="flex-1 p-2 bg-white dark:bg-neutral-800 rounded-lg text-sm break-all border border-neutral-200 dark:border-neutral-700">
                {{ createdKey?.key }}
              </code>
              <Button
                variant="outline"
                size="icon"
                class="flex-shrink-0"
                @click="copyKey"
                :title="t('keys.copy')"
              >
                <Check v-if="copied" class="h-4 w-4 text-green-600" />
                <Copy v-else class="h-4 w-4" />
              </Button>
            </div>
          </div>
          
          <div class="flex justify-end pt-4">
            <Button @click="close" :title="t('common.confirm')">
              <Check class="h-4 w-4 mr-2" />
              {{ t('common.confirm') }}
            </Button>
          </div>
        </div>
      </template>
    </div>
  </Dialog>
</template>