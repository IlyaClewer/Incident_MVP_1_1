<script setup>
import { onMounted } from 'vue'

import { usePatientsStore } from '@/stores/patients'

const store = usePatientsStore()

onMounted(async () => {
  try {
    await store.bootstrap()
  } catch (error) {
    console.error(error)
  }
})
</script>

<template>
  <div class="app-shell">
    <RouterView />
  </div>
</template>

<style scoped>
</style>
