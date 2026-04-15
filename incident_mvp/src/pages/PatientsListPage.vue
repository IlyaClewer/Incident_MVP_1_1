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

        <button
          class="filters-reset-all"
          type="button"
          :disabled="!hasAnyFilters"
          @click="resetAllFilters"
        >
          Сбросить фильтры
        </button>
      </div>

      <div class="toolbar-right toolbar-right--search">
        <input
          v-model="searchDraft"
          class="patients-search"
          placeholder="Поиск по странице"
          @keydown.enter.prevent="applySearch"
        />

        <button
          class="patients-search-btn"
          type="button"
          :disabled="!isSearchDirty"
          @click="applySearch"
        >
          Найти
        </button>

        <button
          v-if="hasSearchValue"
          class="patients-search-reset"
          type="button"
          @click="resetSearch"
        >
          Сброс
        </button>
      </div>
    </div>

    <PatientTable
      :rows="patientRows"
      :stac-cards-by-amb="stacCardsByAmb"
      :search-query="appliedSearchQuery"
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

const searchDraft = computed({
  get: () => store.searchDraft,
  set: (value) => store.setSearchDraft(value),
})

const appliedSearchQuery = computed(() => store.searchQuery)
const isSearchDirty = computed(() => store.searchDraft !== store.searchQuery)
const hasSearchValue = computed(() => Boolean(store.searchDraft || store.searchQuery))
const hasAnyFilters = computed(() =>
  store.selectedExpertGroupId !== 'all' ||
  store.selectedDiagnosisIds.length > 0 ||
  Boolean(store.searchDraft || store.searchQuery) ||
  Boolean(store.patientFilters.ambCard) ||
  Boolean(store.patientFilters.patientName) ||
  Boolean(store.patientFilters.birthDate) ||
  store.patientFilters.departments.length > 0 ||
  store.stacFilters.departmentValues.length > 0 ||
  Boolean(store.stacFilters.dateHosp) ||
  Boolean(store.stacFilters.dateOperation) ||
  Boolean(store.stacFilters.dateDischarge) ||
  store.stacFilters.statuses.length > 0
)

function applySearch() {
  store.applySearchQuery()
}

function resetSearch() {
  store.resetSearchQuery()
}

function resetAllFilters() {
  store.resetAllFilters()
}

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
  position: relative;
  z-index: 5;
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

.toolbar-right--search {
  align-items: center;
}

.patients-search {
  padding: 6px 10px;
  border: 1px solid #c6ccde;
  border-radius: 8px;
  width: 280px;
  font-size: 13px;
  background: #fff;
}

.patients-search-btn,
.patients-search-reset {
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid #2156c4;
  background: #2156c4;
  color: #fff;
  font-size: 13px;
  cursor: pointer;
}

.patients-search-btn:disabled {
  opacity: 0.6;
  cursor: default;
}

.patients-search-reset {
  border-color: #c6ccde;
  background: #fff;
  color: #334155;
}

.filters-reset-all {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid #c6ccde;
  border-radius: 8px;
  background: #fff;
  color: #334155;
  font-size: 13px;
  cursor: pointer;
}

.filters-reset-all::before {
  content: "↺";
  font-size: 13px;
  line-height: 1;
}

.filters-reset-all:hover:not(:disabled) {
  background: #eef4ff;
  border-color: #93c5fd;
}

.filters-reset-all:disabled {
  opacity: 0.55;
  cursor: default;
}
</style>
