<script setup lang="ts">
import { computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ExternalLink, X, RefreshCw, AlertCircle } from 'lucide-vue-next'
import Dialog from '@/components/ui/Dialog.vue'
import MarkdownPreview from '@/components/MarkdownPreview.vue'
import { useArticlePreview } from '@/composables/useArticlePreview'

const props = defineProps<{
  open: boolean
  url: string
  title?: string | null
}>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
}>()

const { t } = useI18n()
const { fetchPreview, reset, content, loading, error } = useArticlePreview()

watch(() => props.open, (isOpen) => {
  if (isOpen && props.url) {
    fetchPreview(props.url)
  } else if (!isOpen) {
    reset()
  }
})

function close(): void {
  emit('update:open', false)
}

const displayTitle = computed(() => {
  if (props.title) return props.title
  try {
    const url = new URL(props.url)
    return url.hostname
  } catch {
    return props.url
  }
})
</script>

<template>
  <Dialog :open="open" size="2xl" @update:open="emit('update:open', $event)">
    <div class="flex flex-col max-h-[80vh]">
      <div class="flex items-center justify-between p-4 border-b border-neutral-200 dark:border-neutral-700">
        <div class="flex-1 min-w-0">
          <h2 class="text-lg font-semibold text-neutral-900 dark:text-neutral-100 truncate">
            {{ displayTitle }}
          </h2>
          <a
            :href="url"
            target="_blank"
            rel="noopener noreferrer"
            class="text-sm text-primary-600 dark:text-primary-400 hover:underline truncate block"
          >
            {{ url }}
          </a>
        </div>
        <div class="flex items-center gap-2">
          <a
            :href="url"
            target="_blank"
            rel="noopener noreferrer"
            :title="t('preview.open_in_new')"
            class="p-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-700 transition-colors"
          >
            <ExternalLink class="h-5 w-5 text-neutral-500 dark:text-neutral-400" />
          </a>
          <button
            class="p-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-700 transition-colors close-btn"
            :title="t('preview.close')"
            @click="close"
          >
            <X class="h-5 w-5 text-neutral-500 dark:text-neutral-400" />
          </button>
        </div>
      </div>

      <div v-if="loading" class="flex-1 flex items-center justify-center py-12">
        <RefreshCw class="h-8 w-8 animate-spin text-primary-500" />
        <span class="ml-3 text-neutral-500">{{ t('preview.loading') }}</span>
      </div>

      <div v-else-if="error" class="flex-1 flex flex-col items-center justify-center py-12">
        <AlertCircle class="h-12 w-12 text-red-500 mb-4" />
        <p class="text-neutral-600 dark:text-neutral-400 text-center">
          {{ t('preview.error') }}
        </p>
        <p class="text-sm text-neutral-500 mt-2">{{ error }}</p>
      </div>

      <div v-else class="flex-1 overflow-auto">
        <MarkdownPreview :content="content" />
      </div>
    </div>
  </Dialog>
</template>