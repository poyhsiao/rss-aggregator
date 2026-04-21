<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Languages, Rss, History, Radio, Settings, Sun, Moon } from 'lucide-vue-next'
import { useTheme } from '@/composables/useTheme'
import { useLocale } from '@/composables/useLocale'
import { useAuthStore } from '@/stores/auth'
import AuthDialog from '@/components/AuthDialog.vue'
import DebugDialog from '@/components/DebugDialog.vue'
import FeatureFlagsDialog from '@/components/FeatureFlagsDialog.vue'
import Button from '@/components/ui/Button.vue'

const route = useRoute()
const { t } = useI18n()
const { isDark, toggleTheme } = useTheme()
const { locale, toggleLocale } = useLocale()
useAuthStore()

// Hidden debug feature: click Feed icon 10 times to open debug dialog
const clickCount = ref(0)
const clickTimer = ref<ReturnType<typeof setTimeout> | null>(null)
const debugDialogOpen = ref(false)

// Hidden feature flags: click Feed icon 10 times on Settings page to open feature flags dialog
const featureFlagsDialogOpen = ref(false)

function handleFeedIconClick(): void {
  // Activate on Settings page for feature flags, Feed page for debug dialog
  const isSettingsPage = route.path === '/settings'
  const isFeedPage = route.path === '/'

  if (!isSettingsPage && !isFeedPage) return

  // Clear previous timer
  if (clickTimer.value) {
    clearTimeout(clickTimer.value)
  }

  clickCount.value++

  // Reset counter after 2 seconds of no clicks
  clickTimer.value = setTimeout(() => {
    clickCount.value = 0
  }, 2000)

  // Open appropriate dialog after 10 clicks
  if (clickCount.value >= 10) {
    if (isSettingsPage) {
      featureFlagsDialogOpen.value = true
    } else if (isFeedPage) {
      debugDialogOpen.value = true
    }
    clickCount.value = 0
    if (clickTimer.value) {
      clearTimeout(clickTimer.value)
      clickTimer.value = null
    }
  }
}

const menuItems = computed(() => {
  const items = [
    { path: '/', label: t('nav.feed'), icon: Rss },
    { path: '/history', label: t('nav.history'), icon: History },
    { path: '/sources', label: t('nav.sources'), icon: Radio },
    { path: '/settings', label: t('common.settings'), icon: Settings },
  ]
  return items
})
</script>

<template>
  <div class="min-h-screen bg-neutral-50 dark:bg-neutral-900">
    <header class="fixed top-0 left-0 right-0 h-16 border-b border-neutral-200 bg-white dark:border-neutral-700 dark:bg-neutral-800 z-40">
      <div class="flex items-center justify-between h-full px-4 md:px-6">
        <div class="flex items-center gap-3">
          <Rss class="h-6 w-6 cursor-pointer select-none" @click="handleFeedIconClick" />
          <span class="font-semibold text-lg hidden sm:block">{{ t('app.name') }}</span>
        </div>
        
        <div class="flex items-center gap-2">
          <Button variant="ghost" size="icon" @click="toggleTheme" :title="t('theme.toggle')">
            <Sun v-if="isDark" class="h-4 w-4" />
            <Moon v-else class="h-4 w-4" />
          </Button>

          <Button variant="ghost" size="icon" @click="toggleLocale" :title="t('language.switch')">
            <Languages class="h-4 w-4" />
            {{ locale === 'zh' ? '中' : 'EN' }}
          </Button>
        </div>
      </div>
    </header>
    
    <div class="flex pt-16">
      <aside class="fixed left-0 top-16 bottom-0 w-64 border-r border-neutral-200 bg-white dark:border-neutral-700 dark:bg-neutral-800 hidden md:block">
        <nav class="p-4 space-y-1">
          <router-link
            v-for="item in menuItems"
            :key="item.path"
            :to="item.path"
            class="flex items-center gap-3 px-3 py-2 rounded-lg text-neutral-600 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-700 transition-colors"
            :class="{
              'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400': route.path === item.path
            }"
          >
            <component :is="item.icon" class="h-5 w-5" />
            <span>{{ item.label }}</span>
          </router-link>
        </nav>
      </aside>
      
      <main class="flex-1 md:ml-64 p-4 md:p-8 pb-20 md:pb-8">
        <slot />
      </main>
    </div>
    
    <nav class="fixed bottom-0 left-0 right-0 h-16 border-t border-neutral-200 bg-white dark:border-neutral-700 dark:bg-neutral-800 md:hidden z-40">
      <div class="flex justify-around h-full">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          class="flex flex-col items-center justify-center gap-1 flex-1 transition-colors"
          :class="route.path === item.path
            ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 font-medium'
            : 'text-neutral-500 dark:text-neutral-400'"
        >
          <component :is="item.icon" class="h-6 w-6" />
          <span class="text-xs">{{ item.label }}</span>
        </router-link>
      </div>
    </nav>
    
    <AuthDialog />
    <DebugDialog v-model:open="debugDialogOpen" />
    <FeatureFlagsDialog v-model:open="featureFlagsDialogOpen" />
  </div>
</template>