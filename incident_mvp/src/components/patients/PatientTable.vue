<template>
  <table class="events-table patients-root-table">
    <thead>
      <tr>
        <TableHeaderCell
          :icon="filterIconUrl"
          :active="Boolean(ambCardFilter)"
        >
          Амб. карта
          <template #filter>
            <input
              v-model="ambCardFilter"
              class="table-filter__input"
              type="text"
              placeholder="Номер амбулаторной карты"
            />
            <button class="table-filter__reset" type="button" @click="ambCardFilter = ''">
              Сбросить
            </button>
          </template>
        </TableHeaderCell>

        <TableHeaderCell
          :icon="filterIconUrl"
          :active="Boolean(patientNameFilter)"
        >
          ФИО
          <template #filter>
            <input
              v-model="patientNameFilter"
              class="table-filter__input"
              type="text"
              placeholder="Фамилия, имя или отчество"
            />
            <button class="table-filter__reset" type="button" @click="patientNameFilter = ''">
              Сбросить
            </button>
          </template>
        </TableHeaderCell>

        <TableHeaderCell
          :icon="filterIconUrl"
          :active="Boolean(birthDateFilter)"
        >
          Дата рождения
          <template #filter>
            <input
              v-model="birthDateFilter"
              class="table-filter__input"
              type="date"
            />
            <button class="table-filter__reset" type="button" @click="birthDateFilter = ''">
              Сбросить
            </button>
          </template>
        </TableHeaderCell>

        <TableHeaderCell
          :icon="filterIconUrl"
          :active="departmentFilter.length > 0"
        >
          Отделение
          <template #filter>
            <div v-if="departmentOptions.length > 0" class="table-filter__checkbox-list">
              <label
                v-for="department in departmentOptions"
                :key="department"
                class="table-filter__checkbox-item"
              >
                <input
                  v-model="departmentFilter"
                  type="checkbox"
                  :value="department"
                />
                <span>{{ department }}</span>
              </label>
            </div>

            <div v-else class="table-filter__empty">Нет доступных отделений</div>

            <button class="table-filter__reset" type="button" @click="departmentFilter = []">
              Сбросить
            </button>
          </template>
        </TableHeaderCell>
      </tr>
    </thead>

    <tbody>
      <template
        v-for="row in rows"
        :key="row.key"
      >
        <PatientRow
          :row="row"
          :is-open="openedAmb === row.key"
          :cards="stacCardsByAmb[row.key] || []"
          :search-query="searchQuery"
          @toggle="togglePatient"
          @open-stac-card="emit('open-stac-card', $event)"
        />
      </template>

      <tr v-if="rows.length === 0">
        <td colspan="4" class="empty-cell">Нет данных</td>
      </tr>
    </tbody>
  </table>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

import filterIconUrl from '@/assets/img/filter.svg'
import { usePatientsStore } from '@/stores/patients'

import PatientRow from './PatientRow.vue'
import TableHeaderCell from './TableHeaderCell.vue'

const props = defineProps({
  rows: { type: Array, required: true },
  stacCardsByAmb: { type: Object, required: true },
  searchQuery: { type: String, default: '' },
})

const emit = defineEmits(['open-stac-card'])

const store = usePatientsStore()
const openedAmb = ref(null)

const ambCardFilter = computed({
  get: () => store.patientFilters.ambCard,
  set: (value) => store.setPatientFilter('ambCard', value),
})

const patientNameFilter = computed({
  get: () => store.patientFilters.patientName,
  set: (value) => store.setPatientFilter('patientName', value),
})

const birthDateFilter = computed({
  get: () => store.patientFilters.birthDate,
  set: (value) => store.setPatientFilter('birthDate', value),
})

const departmentFilter = computed({
  get: () => store.patientFilters.departments,
  set: (value) => store.setPatientFilter('departments', value),
})

const departmentOptions = computed(() => store.patientDepartmentOptions)

watch(
  () => props.rows.map((row) => row.key),
  (keys) => {
    if (openedAmb.value && !keys.includes(openedAmb.value)) {
      openedAmb.value = null
    }
  },
  { immediate: true }
)

function togglePatient(rowKey) {
  openedAmb.value = openedAmb.value === rowKey ? null : rowKey
}
</script>

<style scoped>
.patients-root-table th,
.patients-root-table td {
  white-space: nowrap;
}

.patients-root-table > thead {
  z-index: 900;
}

.empty-cell {
  padding: 12px;
  opacity: 0.7;
}

.table-filter__input {
  width: 100%;
  box-sizing: border-box;
  padding: 8px 10px;
  border: 1px solid #d1d5f0;
  border-radius: 8px;
  font-size: 13px;
}

.table-filter__checkbox-list {
  display: grid;
  gap: 8px;
  max-height: 220px;
  overflow-y: auto;
  margin-bottom: 0;
  padding-right: 2px;
}

.table-filter__checkbox-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.table-filter__empty {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 0;
}

.table-filter__reset {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  margin-top: 2px;
  padding: 9px 12px;
  border: 1px solid rgba(198, 204, 222, 0.95);
  border-radius: 10px;
  background: #f8fafc;
  color: #334155;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
}

.table-filter__reset::before {
  content: "↺";
  font-size: 13px;
  line-height: 1;
}

.table-filter__reset:hover {
  background: #eef4ff;
  border-color: #93c5fd;
}
</style>
