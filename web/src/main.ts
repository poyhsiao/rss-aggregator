import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import i18n from './locales'
import App from './App.vue'
import './styles/main.css'

// Debug: Check if running in Tauri
const isTauri = typeof window !== 'undefined' && '__TAURI__' in window
console.log('[DEBUG] Starting Vue app...')
console.log('[DEBUG] isTauri:', isTauri)
console.log('[DEBUG] window.__TAURI__:', (window as unknown as { __TAURI__?: unknown }).__TAURI__)

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(i18n)

console.log('[DEBUG] Mounting app...')
app.mount('#app')
console.log('[DEBUG] App mounted!')

// Only register service worker in web mode (not Tauri)
if (!isTauri && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(console.error)
  })
}