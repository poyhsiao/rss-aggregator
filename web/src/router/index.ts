import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { isTauri } from '@/utils/environment'
import { isFirstRun } from '@/utils/tauri-bridge'

let setupChecked = false

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/setup',
      name: 'setup',
      component: () => import('@/pages/SetupWizard.vue'),
      meta: { requiresTauri: true, isSetup: true },
    },
    {
      path: '/',
      name: 'feed',
      component: () => import('@/pages/FeedPage.vue'),
    },
    {
      path: '/sources',
      name: 'sources',
      component: () => import('@/pages/SourcesPage.vue'),
    },
    // Redirect old routes to settings with query param
    {
      path: '/keys',
      redirect: () => ({ path: '/settings', query: { tab: 'keys' } }),
    },
    {
      path: '/stats',
      redirect: () => ({ path: '/settings', query: { tab: 'stats' } }),
    },
    {
      path: '/logs',
      redirect: () => ({ path: '/settings', query: { tab: 'stats' } }),
    },
    {
      path: '/history',
      name: 'history',
      component: () => import('@/pages/HistoryPage.vue'),
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/pages/SettingsPage.vue'),
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

router.beforeEach(async (to, _from, next) => {
  if (to.meta.requiresWeb && isTauri()) {
    return next('/')
  }

  if (to.meta.requiresTauri && !isTauri()) {
    return next('/')
  }

  if (isTauri() && !setupChecked && to.name !== 'setup') {
    setupChecked = true
    try {
      const firstRun = await isFirstRun()
      if (firstRun) {
        return next('/setup')
      }
    } catch (e) {
      console.error('[DEBUG Router] isFirstRun error:', e)
    }
  }

  if (to.meta.isSetup) {
    return next()
  }

  const authStore = useAuthStore()

  if (!authStore.isInitialized) {
    await authStore.init()
  }

  next()
})

export default router