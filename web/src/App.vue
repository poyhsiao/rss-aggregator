<script setup lang="ts">
import { onMounted } from 'vue'
import { useTheme } from '@/composables/useTheme'
import { useAuthStore } from '@/stores/auth'
import MainLayout from '@/layouts/MainLayout.vue'
import ToastContainer from '@/components/ui/ToastContainer.vue'

const { init, listenSystemPreference } = useTheme()
const authStore = useAuthStore()

onMounted(() => {
  init()
  listenSystemPreference()
  authStore.init()
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