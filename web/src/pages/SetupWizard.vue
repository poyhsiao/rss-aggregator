<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ArrowLeft, ArrowRight, Check, Globe, Clock, Rss, Database, Loader2 } from 'lucide-vue-next'
import { saveSetupConfig, completeSetup, type SetupConfig } from '@/utils/tauri-bridge'
import { useToast } from '@/composables/useToast'
import { useSettingsStore } from '@/stores/settings'

const router = useRouter()
const { t, locale } = useI18n()
const toast = useToast()
const settingsStore = useSettingsStore()

const currentStep = ref(0)
const isLoading = ref(false)

const steps = [
  { key: 'welcome', icon: Globe },
  { key: 'config', icon: Clock },
  { key: 'sources', icon: Rss },
  { key: 'import', icon: Database },
  { key: 'complete', icon: Check },
]

const config = ref<SetupConfig>({
  timezone: 'Asia/Taipei',
  language: 'en',
})

const defaultSources = ref<Array<{ name: string; url: string; enabled: boolean }>>([])
const importPath = ref('')
const importProgress = ref(0)

const timezoneOptions = [
  'Asia/Taipei',
  'Asia/Tokyo',
  'Asia/Shanghai',
  'Asia/Singapore',
  'America/New_York',
  'America/Los_Angeles',
  'Europe/London',
  'Europe/Paris',
  'UTC',
]

type AppLocale = 'zh' | 'en'

const canProceed = computed(() => {
  switch (currentStep.value) {
    case 0:
      return true
    case 1:
      return config.value.timezone !== '' && config.value.language !== ''
    case 2:
      return true
    case 3:
      return true
    default:
      return true
  }
})

const progressPercent = computed(() => {
  return ((currentStep.value + 1) / steps.length) * 100
})

async function nextStep() {
  if (currentStep.value === 1) {
    const lang = config.value.language as AppLocale
    locale.value = lang
    settingsStore.locale = lang
  }
  
  if (currentStep.value < steps.length - 2) {
    currentStep.value++
  } else if (currentStep.value === steps.length - 2) {
    await finishSetup()
  }
}

function prevStep() {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

async function finishSetup() {
  isLoading.value = true
  importProgress.value = 0
  
  try {
    importProgress.value = 20
    await saveSetupConfig(config.value)
    
    importProgress.value = 50
    
    importProgress.value = 80
    await completeSetup()
    
    importProgress.value = 100
    currentStep.value = steps.length - 1
  } catch (error) {
    toast.error(String(error))
  } finally {
    isLoading.value = false
  }
}

function goToApp() {
  router.replace('/')
}

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) {
    importPath.value = (file as unknown as { path?: string }).path || file.name
  }
}

function addDefaultSource() {
  defaultSources.value.push({
    name: '',
    url: '',
    enabled: true,
  })
}

function removeSource(index: number) {
  defaultSources.value.splice(index, 1)
}
</script>

<template>
  <div class="min-h-screen bg-background flex flex-col">
    <div class="p-4 border-b">
      <div class="max-w-2xl mx-auto">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm text-muted-foreground">
            {{ t('setup.step') }} {{ currentStep + 1 }} / {{ steps.length }}
          </span>
          <span class="text-sm text-muted-foreground">
            {{ Math.round(progressPercent) }}%
          </span>
        </div>
        <div class="h-2 bg-muted rounded-full overflow-hidden">
          <div
            class="h-full bg-primary transition-all duration-300"
            :style="{ width: `${progressPercent}%` }"
          />
        </div>
      </div>
    </div>

    <div class="flex-1 flex items-center justify-center p-6">
      <div class="w-full max-w-2xl">
        
        <div v-if="currentStep === 0" class="text-center space-y-6">
          <div class="w-20 h-20 mx-auto bg-primary/10 rounded-full flex items-center justify-center">
            <Globe class="w-10 h-10 text-primary" />
          </div>
          <h1 class="text-3xl font-bold">{{ t('setup.welcome.title') }}</h1>
          <p class="text-muted-foreground max-w-md mx-auto">
            {{ t('setup.welcome.description') }}
          </p>
        </div>

        <div v-else-if="currentStep === 1" class="space-y-6">
          <div class="text-center space-y-2">
            <div class="w-16 h-16 mx-auto bg-primary/10 rounded-full flex items-center justify-center">
              <Clock class="w-8 h-8 text-primary" />
            </div>
            <h2 class="text-2xl font-bold">{{ t('setup.config.title') }}</h2>
            <p class="text-muted-foreground">{{ t('setup.config.description') }}</p>
          </div>

          <div class="space-y-4 max-w-md mx-auto">
            <div>
              <label class="block text-sm font-medium mb-2">{{ t('setup.config.language') }}</label>
              <select
                v-model="config.language"
                class="w-full px-3 py-2 border rounded-md bg-background"
              >
                <option value="en">English</option>
                <option value="zh">中文</option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium mb-2">{{ t('setup.config.timezone') }}</label>
              <select
                v-model="config.timezone"
                class="w-full px-3 py-2 border rounded-md bg-background"
              >
                <option v-for="tz in timezoneOptions" :key="tz" :value="tz">
                  {{ tz }}
                </option>
              </select>
            </div>
          </div>
        </div>

        <div v-else-if="currentStep === 2" class="space-y-6">
          <div class="text-center space-y-2">
            <div class="w-16 h-16 mx-auto bg-primary/10 rounded-full flex items-center justify-center">
              <Rss class="w-8 h-8 text-primary" />
            </div>
            <h2 class="text-2xl font-bold">{{ t('setup.sources.title') }}</h2>
            <p class="text-muted-foreground">{{ t('setup.sources.description') }}</p>
          </div>

          <div class="space-y-4 max-w-lg mx-auto">
            <div v-if="defaultSources.length === 0" class="text-center py-8 text-muted-foreground">
              <p>{{ t('setup.sources.empty') }}</p>
            </div>

            <div v-for="(source, index) in defaultSources" :key="index" class="flex gap-2 items-start">
              <div class="flex-1 space-y-2">
                <input
                  v-model="source.name"
                  type="text"
                  :placeholder="t('setup.sources.name_placeholder')"
                  class="w-full px-3 py-2 border rounded-md bg-background"
                />
                <input
                  v-model="source.url"
                  type="url"
                  :placeholder="t('setup.sources.url_placeholder')"
                  class="w-full px-3 py-2 border rounded-md bg-background"
                />
              </div>
              <button
                class="px-3 py-2 text-destructive hover:bg-destructive/10 rounded-md"
                @click="removeSource(index)"
              >
                {{ t('common.delete') }}
              </button>
            </div>

            <button
              class="w-full px-4 py-2 border border-dashed rounded-md hover:bg-muted/50"
              @click="addDefaultSource"
            >
              + {{ t('setup.sources.add') }}
            </button>

            <p class="text-sm text-muted-foreground text-center">
              {{ t('setup.sources.skip_hint') }}
            </p>
          </div>
        </div>

        <div v-else-if="currentStep === 3" class="space-y-6">
          <div class="text-center space-y-2">
            <div class="w-16 h-16 mx-auto bg-primary/10 rounded-full flex items-center justify-center">
              <Database class="w-8 h-8 text-primary" />
            </div>
            <h2 class="text-2xl font-bold">{{ t('setup.import.title') }}</h2>
            <p class="text-muted-foreground">{{ t('setup.import.description') }}</p>
          </div>

          <div class="space-y-4 max-w-md mx-auto">
            <label class="block">
              <div class="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer hover:bg-muted/50 transition-colors">
                <Database class="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
                <p class="text-sm text-muted-foreground mb-2">{{ t('setup.import.select_file') }}</p>
                <input
                  type="file"
                  accept=".db,.sqlite,.sqlite3"
                  class="hidden"
                  @change="handleFileSelect"
                />
              </div>
            </label>

            <div v-if="importPath" class="p-3 bg-muted rounded-md">
              <p class="text-sm">{{ importPath }}</p>
            </div>

            <p class="text-sm text-muted-foreground text-center">
              {{ t('setup.import.skip_hint') }}
            </p>
          </div>
        </div>

        <div v-else-if="currentStep === 4" class="space-y-6">
          <div v-if="isLoading" class="text-center space-y-4">
            <Loader2 class="w-12 h-12 mx-auto animate-spin text-primary" />
            <p class="text-muted-foreground">{{ t('setup.progress.initializing') }}</p>
            <div class="w-full max-w-xs mx-auto h-2 bg-muted rounded-full overflow-hidden">
              <div
                class="h-full bg-primary transition-all duration-300"
                :style="{ width: `${importProgress}%` }"
              />
            </div>
          </div>

          <div v-else class="text-center space-y-6">
            <div class="w-20 h-20 mx-auto bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center">
              <Check class="w-10 h-10 text-green-600 dark:text-green-400" />
            </div>
            <h1 class="text-3xl font-bold">{{ t('setup.complete.title') }}</h1>
            <p class="text-muted-foreground max-w-md mx-auto">
              {{ t('setup.complete.description') }}
            </p>
            <button
              class="px-8 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
              @click="goToApp"
            >
              {{ t('setup.complete.start') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="currentStep < 4" class="p-4 border-t">
      <div class="max-w-2xl mx-auto flex justify-between">
        <button
          v-if="currentStep > 0"
          class="px-4 py-2 border rounded-md hover:bg-muted/50 flex items-center gap-2"
          @click="prevStep"
        >
          <ArrowLeft class="w-4 h-4" />
          {{ t('setup.back') }}
        </button>
        <div v-else />

        <button
          :disabled="!canProceed || isLoading"
          class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          @click="nextStep"
        >
          <template v-if="currentStep === steps.length - 2">
            <Loader2 v-if="isLoading" class="w-4 h-4 animate-spin" />
            <Check v-else class="w-4 h-4" />
            {{ t('setup.finish') }}
          </template>
          <template v-else>
            {{ t('setup.next') }}
            <ArrowRight class="w-4 h-4" />
          </template>
        </button>
      </div>
    </div>
  </div>
</template>