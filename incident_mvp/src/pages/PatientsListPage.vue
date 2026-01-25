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

        <select
          class="expert-group-select"
          v-model="selectedGroupId"
        >
          <option v-for="g in expertGroups" :key="g.id" :value="g.id">
            {{ g.title }}
          </option>
        </select>

        <DiagnosisDropdown
          :diagnoses="availableDiagnoses"
          v-model="selectedDiagnosisIds"
        />
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
import DiagnosisDropdown from '@/components/filters/DiagnosisDropdown.vue'

const router = useRouter()
const store = usePatientsStore()

const expertGroups = computed(() => store.expertGroups)

const selectedGroupId = computed({
  get: () => store.selectedExpertGroupId,
  set: (val) => store.setExpertGroup(val),
})

// список диагнозов для dropdown — уже учитывает выбранную эксперт-группу
const availableDiagnoses = computed(() => store.availableDiagnosesForFilter ?? [])

const selectedDiagnosisIds = computed({
  get: () => store.selectedDiagnosisIds,
  set: (val) => store.setSelectedDiagnosisIds(val),
})

const patients = computed(() => store.filteredStacCards)

function openStacCard(stacCardId) {
  const g = store.selectedExpertGroupId
  const dx = store.selectedDiagnosisIds?.[0] // открываем первым выбранный диагноз

  router.push({
    name: 'patient',
    params: { id: String(stacCardId) },
    query: {
      ...(g ? { g } : {}),
      ...(dx ? { dx } : {}),
    },
  })
}
</script>

<style scoped>
.toolbar-left--home {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
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
