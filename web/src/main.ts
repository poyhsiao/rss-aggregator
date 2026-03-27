import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import i18n from './locales'
import App from './App.vue'
import './styles/main.css'

const isTauri = typeof window !== 'undefined' && '__TAURI__' in window
const isDev = import.meta.env.DEV

console.log('[DEBUG] Starting Vue app...')
console.log('[DEBUG] isTauri:', isTauri)
console.log('[DEBUG] isDev:', isDev)

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(i18n)

console.log('[DEBUG] Mounting app...')
app.mount('#app')
console.log('[DEBUG] App mounted!')

if (!isTauri && !isDev && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(console.error)
  })
}