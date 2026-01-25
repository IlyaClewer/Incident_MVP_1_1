


<script setup>
import { onMounted } from 'vue'
import { usePatientsStore } from '@/stores/patients'

const store = usePatientsStore()

onMounted(() => {
  store.fetchPatients()
  store.fetchMeta()
})
</script>

<template>
  <div class="app-shell">
    <RouterView />
  </div>
</template>


<style scoped>

</style>
