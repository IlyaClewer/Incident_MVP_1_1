<template>
  <table class="stac-table">
    <thead>
      <tr>
        <th>№ стац. карты</th>

        <TableHeaderCell
          :icon="filterIconUrl"
          inner
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

        <TableHeaderCell
          :icon="filterIconUrl"
          inner
          :active="Boolean(dateHospFilter)"
        >
          Дата госпитализации
          <template #filter>
            <input
              v-model="dateHospFilter"
              class="table-filter__input"
              type="date"
            />
            <button class="table-filter__reset" type="button" @click="dateHospFilter = ''">
              Сбросить
            </button>
          </template>
        </TableHeaderCell>

        <TableHeaderCell
          :icon="filterIconUrl"
          inner
          :active="Boolean(dateOperationFilter)"
        >
          Дата операции
          <template #filter>
            <input
              v-model="dateOperationFilter"
              class="table-filter__input"
              type="date"
            />
            <button class="table-filter__reset" type="button" @click="dateOperationFilter = ''">
              Сбросить
            </button>
          </template>
        </TableHeaderCell>

        <TableHeaderCell
          :icon="filterIconUrl"
          inner
          :active="Boolean(dateDischargeFilter)"
        >
          Дата выписки
          <template #filter>
            <input
              v-model="dateDischargeFilter"
              class="table-filter__input"
              type="date"
            />
            <button class="table-filter__reset" type="button" @click="dateDischargeFilter = ''">
              Сбросить
            </button>
          </template>
        </TableHeaderCell>

        <TableHeaderCell
          :icon="filterIconUrl"
          inner
          :active="statusFilter.length > 0"
        >
          Статус
          <template #filter>
            <div class="table-filter__checkbox-list">
              <label
                v-for="status in statusOptions"
                :key="status.value"
                class="table-filter__checkbox-item"
              >
                <input
                  v-model="statusFilter"
                  type="checkbox"
                  :value="status.value"
                />
                <span>{{ status.label }}</span>
              </label>
            </div>

            <button class="table-filter__reset" type="button" @click="statusFilter = []">
              Сбросить
            </button>
          </template>
        </TableHeaderCell>
      </tr>
    </thead>

    <tbody>
      <tr
        v-for="card in cards"
        :key="card.id"
        class="stac-row"
        @click.stop="emit('open-stac-card', card.id)"
      >
        <td class="stac-link">
          <HighlightedText :text="card.cardNumber" :query="searchQuery" />
        </td>
        <td class="cell-center">
          <HighlightedText :text="card.department ?? '—'" :query="searchQuery" />
        </td>
        <td class="cell-center">
          <HighlightedText :text="formatDate(card.date_hosp)" :query="searchQuery" />
        </td>
        <td class="cell-center">
          <HighlightedText :text="formatDate(card.date_operation)" :query="searchQuery" />
        </td>
        <td class="cell-center">
          <HighlightedText :text="formatDate(card.date_discharge)" :query="searchQuery" />
        </td>
        <td class="status-cell status-cell--center" :data-status="card.status ?? 'new'">
          <span class="status-pill">
            <HighlightedText :text="formatStatusLabel(card.status)" :query="searchQuery" />
          </span>
        </td>
      </tr>

      <tr v-if="cards.length === 0">
        <td colspan="6" class="stac-empty">Нет стац. карт</td>
      </tr>
    </tbody>
  </table>
</template>

<script setup>
import { computed } from 'vue'

import filterIconUrl from '@/assets/img/filter.svg'
import HighlightedText from '@/components/ui/HighlightedText.vue'
import { usePatientsStore } from '@/stores/patients'
import { formatDate } from '@/utils/dateFormatter'

import TableHeaderCell from './TableHeaderCell.vue'

defineProps({
  cards: { type: Array, required: true },
  searchQuery: { type: String, default: '' },
})

const emit = defineEmits(['open-stac-card'])

const store = usePatientsStore()

const departmentFilter = computed({
  get: () => store.stacFilters.departmentValues,
  set: (value) => store.setStacFilter('departmentValues', value),
})

const dateHospFilter = computed({
  get: () => store.stacFilters.dateHosp,
  set: (value) => store.setStacFilter('dateHosp', value),
})

const dateOperationFilter = computed({
  get: () => store.stacFilters.dateOperation,
  set: (value) => store.setStacFilter('dateOperation', value),
})

const dateDischargeFilter = computed({
  get: () => store.stacFilters.dateDischarge,
  set: (value) => store.setStacFilter('dateDischarge', value),
})

const statusFilter = computed({
  get: () => store.stacFilters.statuses,
  set: (value) => store.setStacFilter('statuses', value),
})

const departmentOptions = computed(() => store.stacDepartmentOptions)
const statusOptions = computed(() => store.stacStatusOptions)

function formatStatusLabel(status) {
  switch (String(status ?? '').toLowerCase()) {
    case 'confirmed':
    case 'approved':
    case 'accepted':
      return 'Подтвержден'
    case 'rejected':
      return 'Отклонен'
    default:
      return 'Новый'
  }
}
</script>

<style scoped>
.stac-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: auto;
  background: #fff;
  border: 1px solid rgba(198, 204, 222, 0.75);
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.06);
  border-radius: 10px;
  overflow: visible;
  position: relative;
  z-index: 20;
}

.stac-table th,
.stac-table td {
  width: auto;
  padding: 6px 8px;
  border-bottom: 1px solid rgba(198, 204, 222, 0.55);
  border-right: 1px solid rgba(198, 204, 222, 0.45);
  background: #fff;
  font-size: 12px;
  vertical-align: middle;
  white-space: nowrap;
}

.stac-table th:last-child,
.stac-table td:last-child {
  border-right: none;
}

.stac-table tbody tr:last-child td {
  border-bottom: none;
}

.stac-table thead th {
  background: linear-gradient(180deg, #f9fbff 0%, #f0f4fb 100%);
  font-weight: 700;
}

.stac-row {
  cursor: pointer;
}

.stac-row:hover td {
  background: #eef4ff;
}

.stac-link {
  color: #2156c4;
  text-decoration: underline;
  white-space: nowrap;
}

.cell-center {
  text-align: center;
}

.status-cell--center {
  text-align: center;
}

.status-cell--center .status-pill {
  margin: 0 auto;
}

.stac-empty {
  padding: 10px;
  opacity: 0.7;
  text-align: center;
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
