<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import Dialog from '@/components/ui/Dialog.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'

const { t } = useI18n()
const authStore = useAuthStore()

const apiKey = ref('')
const error = ref<string | null>(null)
const isVerifying = ref(false)

async function handleVerify(): Promise<void> {
  if (!apiKey.value.trim()) return
  
  isVerifying.value = true
  error.value = null
  
  try {
    const isValid = await authStore.verifyKey(apiKey.value.trim())
    if (!isValid) {
      error.value = authStore.error === 'invalid' ? t('auth.invalid') : t('auth.failed')
    }
  } finally {
    isVerifying.value = false
  }
}
</script>

<template>
  <Dialog :open="!authStore.isValid">
    <div class="p-6">
      <div class="mb-6">
        <h2 class="text-xl font-semibold flex items-center gap-2">
          🔐 {{ t('auth.title') }}
        </h2>
        <p class="text-neutral-500 dark:text-neutral-400 mt-1">
          {{ t('auth.description') }}
        </p>
      </div>
      
      <div class="space-y-4">
        <Input
          v-model="apiKey"
          type="password"
          :placeholder="t('auth.placeholder')"
          :disabled="isVerifying"
          @keyup.enter="handleVerify"
        />
        
        <p v-if="error" class="text-sm text-red-500 dark:text-red-400">
          {{ error }}
        </p>
      </div>
      
      <div class="mt-6">
        <Button 
          class="w-full"
          :disabled="!apiKey || isVerifying"
          @click="handleVerify"
        >
          <span v-if="isVerifying">{{ t('auth.verifying') }}</span>
          <span v-else>{{ t('auth.verify') }}</span>
        </Button>
      </div>
    </div>
  </Dialog>
</template>