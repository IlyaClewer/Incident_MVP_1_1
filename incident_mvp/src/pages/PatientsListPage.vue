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

        <!-- Новый фильтр: мультивыбор диагнозов -->
        <DiagnosisDropdown
            :diagnoses="availableDiagnoses ?? []"
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

// v-model для select группы (через action, чтобы сбрасывать диагнозы при смене группы)
const selectedGroupId = computed({
  get: () => store.selectedExpertGroupId,
  set: (val) => store.setExpertGroup(val),
})

// диагнози, разрешённые для текущей группы (или все, если группа "Все")
const availableDiagnoses = computed(() => {
  const all = store.diagnoses ?? []
  const gid = store.selectedExpertGroupId

  if (!gid || gid === 'all') return all

  const g = (store.expertGroups ?? []).find(x => x.id === gid)
  const allowed = new Set(g?.diagnosis_ids ?? [])
  return all.filter(d => allowed.has(d.id))
})


// v-model для мультивыбора диагнозов (компонент DiagnosisDropdown должен эмитить update:modelValue)
const selectedDiagnosisIds = computed({
  get: () => store.selectedDiagnosisIds,
  set: (val) => store.setSelectedDiagnosisIds(val),
})

// важно: теперь это именно отфильтрованные стац-карты
const patients = computed(() => store.filteredStacCards)

function openStacCard(stacCardId) {
  router.push({ name: 'patient', params: { id: String(stacCardId) } })
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
