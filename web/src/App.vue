<script setup lang="ts">
import { onMounted } from 'vue'
import { useTheme } from '@/composables/useTheme'
import MainLayout from '@/layouts/MainLayout.vue'
import ToastContainer from '@/components/ui/ToastContainer.vue'

const { init, listenSystemPreference } = useTheme()

onMounted(() => {
  init()
  listenSystemPreference()
})
</script>

<template>
  <MainLayout>
    <router-view />
  </MainLayout>
  <ToastContainer />
</template>