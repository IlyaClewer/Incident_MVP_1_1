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
        <span id="visible-count">{{ visibleCards.length }}</span> записей

        <select
          v-model="selectedGroupId"
          class="expert-group-select"
        >
          <option
            v-for="group in expertGroups"
            :key="group.id"
            :value="group.id"
          >
            {{ group.title }}
          </option>
        </select>

        <DiagnosisDropdown
          v-model="selectedDiagnosisIds"
          :diagnoses="availableDiagnoses"
        />
      </div>

      <div class="toolbar-right">
        <input
          v-model="searchQuery"
          class="patients-search"
          placeholder="Поиск по странице"
        />
      </div>
    </div>

    <PatientTable
      :rows="patientRows"
      :stac-cards-by-amb="stacCardsByAmb"
      :search-query="searchQuery"
      @open-stac-card="openStacCard"
    />
  </main>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import DiagnosisDropdown from '@/components/filters/DiagnosisDropdown.vue'
import PatientTable from '@/components/patients/PatientTable.vue'
import { usePatientsStore } from '@/stores/patients'

const router = useRouter()
const store = usePatientsStore()

const expertGroups = computed(() => store.expertGroups)
const availableDiagnoses = computed(() => store.availableDiagnosesForFilter ?? [])
const visibleCards = computed(() => store.filteredStacCards)
const patientRows = computed(() => store.filteredPatientRows)
const stacCardsByAmb = computed(() => store.stacCardsByAmb)

const selectedGroupId = computed({
  get: () => store.selectedExpertGroupId,
  set: (value) => store.setExpertGroup(value),
})

const selectedDiagnosisIds = computed({
  get: () => store.selectedDiagnosisIds,
  set: (value) => store.setSelectedDiagnosisIds(value),
})

const searchQuery = computed({
  get: () => store.searchQuery,
  set: (value) => store.setSearchQuery(value),
})

function openStacCard(stacCardId) {
  const expertGroupId = store.selectedExpertGroupId
  const diagnosisId = store.selectedDiagnosisIds?.[0]

  router.push({
    name: 'patient',
    params: { id: String(stacCardId) },
    query: {
      ...(expertGroupId ? { g: expertGroupId } : {}),
      ...(diagnosisId ? { dx: diagnosisId } : {}),
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

.expert-group-select:focus,
.patients-search:focus {
  outline: none;
  border-color: #2156c4;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
}

.patients-search {
  padding: 6px 10px;
  border: 1px solid #c6ccde;
  border-radius: 8px;
  width: 280px;
  font-size: 13px;
  background: #fff;
}
</style>
