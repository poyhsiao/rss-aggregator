import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { setLocale } from '@/locales'

export function useLocale() {
  const { locale, t } = useI18n()

  const currentLocale = computed(() => locale.value)
  
  const isZh = computed(() => locale.value === 'zh')
  const isEn = computed(() => locale.value === 'en')

  function changeLocale(newLocale: 'zh' | 'en'): void {
    setLocale(newLocale)
  }

  function toggleLocale(): void {
    const newLocale = locale.value === 'zh' ? 'en' : 'zh'
    setLocale(newLocale)
  }

  return {
    locale: currentLocale,
    isZh,
    isEn,
    t,
    changeLocale,
    toggleLocale,
  }
}