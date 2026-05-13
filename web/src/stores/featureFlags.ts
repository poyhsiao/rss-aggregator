import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useFeatureFlagsStore = defineStore('featureFlags', () => {
  const groupsEnabled = ref<boolean>(
    localStorage.getItem('ff_groups_enabled') !== 'false'
  )
  const groupSchedulesEnabled = ref<boolean>(
    localStorage.getItem('ff_group_schedules_enabled') !== 'false'
  )

  watch(groupsEnabled, (val) => {
    localStorage.setItem('ff_groups_enabled', String(val))
    if (!val) {
      groupSchedulesEnabled.value = false
      localStorage.setItem('ff_group_schedules_enabled', 'false')
    }
  })

  watch(groupSchedulesEnabled, (val) => {
    localStorage.setItem('ff_group_schedules_enabled', String(val))
  })

  return { groupsEnabled, groupSchedulesEnabled }
})