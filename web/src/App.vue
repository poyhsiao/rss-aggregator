<script setup lang="ts">
import { onMounted } from 'vue'
import { useTheme } from '@/composables/useTheme'
import { useFeatureFlagsStore } from '@/stores/featureFlags'
import MainLayout from '@/layouts/MainLayout.vue'
import ToastContainer from '@/components/ui/ToastContainer.vue'

const { init: initTheme, listenSystemPreference } = useTheme()
const featureFlagsStore = useFeatureFlagsStore()

let initialized = false

onMounted(() => {
  initTheme()
  listenSystemPreference()
  if (!initialized) {
    initialized = true
    featureFlagsStore.init()
  }
})
</script>

<template>
  <MainLayout>
    <router-view v-slot="{ Component, route }">
      <Transition name="fade" mode="out-in">
        <component :is="Component" :key="route.path" />
      </Transition>
    </router-view>
  </MainLayout>
  <ToastContainer />
</template>