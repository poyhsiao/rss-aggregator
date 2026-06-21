<script setup lang="ts">
import { computed } from 'vue'
import { X } from 'lucide-vue-next'
import Dialog from '@/components/ui/Dialog.vue'
import { useFeedUrlSettingsStore } from '@/stores/feedUrlSettings'

defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
}>()

const store = useFeedUrlSettingsStore()

const isEnabled = computed(() => store.enabled)

async function toggle() {
  await store.setEnabled(!isEnabled.value)
}

function close() {
  emit('update:open', false)
}
</script>

<template>
  <Dialog
    :open="open"
    data-testid="feature-dialog"
    @update:open="emit('update:open', $event)"
  >
    <div class="p-4">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-semibold">功能設定</h3>
        <button
          data-testid="close-btn"
          class="p-1 rounded border border-gray-300"
          @click="close"
        >
          <X class="w-4 h-4" />
        </button>
      </div>

      <div class="flex justify-between items-center p-3 border rounded-lg bg-gray-50">
        <div>
          <div class="font-medium">啟用 Feed URL 功能</div>
          <div class="text-sm text-gray-500">在 Preview Dialog 中顯示 RSS/JSON/Markdown URL</div>
        </div>
        <button
          data-testid="feature-toggle"
          :class="[
            'relative w-12 h-6 rounded-full transition-colors',
            isEnabled ? 'bg-blue-500' : 'bg-gray-300',
          ]"
          @click="toggle"
        >
          <span
            :class="[
              'absolute top-1 w-4 h-4 bg-white rounded-full transition-transform',
              isEnabled ? 'translate-x-7' : 'translate-x-1',
            ]"
          />
        </button>
      </div>

      <div class="mt-4 p-3 bg-yellow-50 rounded text-sm">
        <strong>💡 提示：</strong>啟用後，請在 Preview Dialog 中點擊展開按鈕查看 URL
      </div>
    </div>
  </Dialog>
</template>
