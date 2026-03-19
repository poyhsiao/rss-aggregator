import { createI18n } from 'vue-i18n'
import zh from './zh.json'
import en from './en.json'

const STORAGE_KEY = 'rss-locale'

function getDefaultLocale(): string {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored) return stored
  
  const browserLang = navigator.language.toLowerCase()
  if (browserLang.startsWith('zh')) return 'zh'
  return 'en'
}

const i18n = createI18n({
  legacy: false,
  locale: getDefaultLocale(),
  fallbackLocale: 'en',
  messages: {
    zh,
    en,
  },
})

export function setLocale(newLocale: 'zh' | 'en'): void {
  i18n.global.locale.value = newLocale
  localStorage.setItem(STORAGE_KEY, newLocale)
  document.documentElement.lang = newLocale === 'zh' ? 'zh-Hant' : 'en'
}

export default i18n