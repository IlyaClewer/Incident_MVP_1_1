<template>
  <header class="topbar">
    <div class="topbar__left">
      <button class="topbar__menu-btn">☰</button>
      <span class="topbar__app-short">Incident MVP</span>
    </div>

    <div class="topbar__right">Прототип</div>
  </header>

  <main class="page-container">
    <div class="toolbar">
      <div class="toolbar-left toolbar-left--home">
        <span id="visible-count">{{ patients.length }}</span> записей

        <select class="expert-group-select">
          <option selected>Экспертная группа A</option>
          <option>Экспертная группа B</option>
          <option>Экспертная группа C</option>
          <option>Экспертная группа D</option>
          <option>Экспертная группа E</option>
          <option>Экспертная группа F</option>
          <option>Экспертная группа G</option>
          <option>Экспертная группа H</option>
          <option>Экспертная группа I</option>
          <option>Экспертная группа J</option>
        </select>
      </div>

      <div class="toolbar-right">
        <input class="patients-search" placeholder="Поиск " disabled />
      </div>
    </div>

    <PatientTable :patients="patients" @open-stac-card="openStacCard" />
  </main>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { usePatientsStore } from '@/stores/patients'
import PatientTable from '@/components/patients/PatientTable.vue'

const router = useRouter()
const store = usePatientsStore()

const patients = computed(() => store.patientsWithEvents)

function openStacCard(stacCardId) {
  router.push({ name: 'patient', params: { id: String(stacCardId) } })
}
</script>

<style scoped>
.toolbar-left--home {
  display: flex;
  align-items: center;
  gap: 12px;
}

.expert-group-select {
  padding: 6px 10px;
  border: 1px solid #c6ccde;
  border-radius: 8px;
  font-size: 13px;
  background: #fff;
}

.expert-group-select:focus {
  outline: none;
  border-color: #2156c4;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
}

.patients-search {
  padding: 6px 10px;
  border: 1px solid #c6ccde;
  border-radius: 8px;
  width: 260px;
  font-size: 13px;
  background: #fff;
  opacity: 0.7;
}
</style>
