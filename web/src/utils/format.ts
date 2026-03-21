import { useI18n } from 'vue-i18n'

export function formatDate(dateString: string): string {
  const { t, locale } = useI18n()
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  
  if (minutes < 1) return t('time.just_now')
  if (minutes < 60) return t('time.minutes_ago', { count: minutes })
  if (hours < 24) return t('time.hours_ago', { count: hours })
  if (days < 7) return t('time.days_ago', { count: days })
  
  const localeStr = locale.value === 'zh' ? 'zh-TW' : 'en-US'
  return date.toLocaleDateString(localeStr, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}