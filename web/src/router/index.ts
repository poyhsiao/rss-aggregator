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
  console.log('[DEBUG Router] Navigating to:', to.path)
  console.log('[DEBUG Router] isTauri():', isTauri())
  
  if (to.meta.requiresWeb && isTauri()) {
    console.log('[DEBUG Router] Route requires web but in Tauri, redirecting to /')
    return next('/')
  }

  if (to.meta.requiresTauri && !isTauri()) {
    console.log('[DEBUG Router] Route requires Tauri but not in Tauri, redirecting to /')
    return next('/')
  }

  if (isTauri() && !setupChecked && to.name !== 'setup') {
    setupChecked = true
    console.log('[DEBUG Router] Checking first run...')
    try {
      const firstRun = await isFirstRun()
      console.log('[DEBUG Router] isFirstRun:', firstRun)
      if (firstRun) {
        console.log('[DEBUG Router] First run, redirecting to /setup')
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
    console.log('[DEBUG Router] Initializing auth store...')
    await authStore.init()
    console.log('[DEBUG Router] Auth store initialized')
  }
  
  console.log('[DEBUG Router] Proceeding to:', to.path)
  next()
})

export default router