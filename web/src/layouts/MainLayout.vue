<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Languages } from 'lucide-vue-next'
import { useTheme } from '@/composables/useTheme'
import { useLocale } from '@/composables/useLocale'
import { useAuthStore } from '@/stores/auth'
import AuthDialog from '@/components/AuthDialog.vue'
import Button from '@/components/ui/Button.vue'

const route = useRoute()
const { t } = useI18n()
const { isDark, toggleTheme } = useTheme()
const { locale, toggleLocale } = useLocale()
useAuthStore()

const menuItems = computed(() => [
  { path: '/', label: t('nav.feed'), icon: '📰' },
  { path: '/sources', label: t('nav.sources'), icon: '📡' },
  { path: '/keys', label: t('nav.keys'), icon: '🔑' },
  { path: '/stats', label: t('nav.stats'), icon: '📊' },
  { path: '/logs', label: t('nav.logs'), icon: '📝' },
])
</script>

<template>
  <div class="min-h-screen bg-neutral-50 dark:bg-neutral-900">
    <header class="fixed top-0 left-0 right-0 h-16 border-b border-neutral-200 bg-white dark:border-neutral-700 dark:bg-neutral-800 z-40">
      <div class="flex items-center justify-between h-full px-4 md:px-6">
        <div class="flex items-center gap-3">
          <span class="text-xl">📰</span>
          <span class="font-semibold text-lg hidden sm:block">RSS Aggregator</span>
        </div>
        
        <div class="flex items-center gap-2">
          <Button variant="ghost" size="icon" @click="toggleTheme" :title="t('theme.toggle')">
            <span v-if="isDark">☀️</span>
            <span v-else>🌙</span>
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
            <span class="text-lg">{{ item.icon }}</span>
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
          class="flex flex-col items-center justify-center gap-1 text-neutral-500 dark:text-neutral-400"
          :class="{ 'text-primary-500': route.path === item.path }"
        >
          <span class="text-xl">{{ item.icon }}</span>
          <span class="text-xs">{{ item.label }}</span>
        </router-link>
      </div>
    </nav>
    
    <AuthDialog />
  </div>
</template>