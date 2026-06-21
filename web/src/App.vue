<script setup lang="ts">
import { onMounted } from 'vue'
import { useTheme } from '@/composables/useTheme'
import { useAuthStore } from '@/stores/auth'
import { useFeatureFlagsStore } from '@/stores/featureFlags'
import MainLayout from '@/layouts/MainLayout.vue'
import ToastContainer from '@/components/ui/ToastContainer.vue'

const { init, listenSystemPreference } = useTheme()
const authStore = useAuthStore()
const featureFlagsStore = useFeatureFlagsStore()

onMounted(async () => {
  init()
  listenSystemPreference()
  await authStore.init()
  // Seed feature flags from backend so pages see correct values on load
  featureFlagsStore.fetchSettings().catch(() => {
    /* non-blocking — use localStorage defaults as fallback */
  })
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