



<script setup>
import { onMounted } from 'vue'
import { usePatientsStore } from '@/stores/patients'

const store = usePatientsStore()

onMounted(() => {
  // если у тебя уже есть action ensureLoaded/fetchPatients — вызывай её
  store.fetchPatients()
})
</script>

<template>
  <div class="app-shell">
    <RouterView />
  </div>
</template>


<style scoped>

</style>
