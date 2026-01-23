<template>
  <table class="events-table patients-root-table">
    <thead>
      <tr>
        <TableHeaderCell :icon="filterIconUrl">Амб. карта</TableHeaderCell>
        <TableHeaderCell :icon="filterIconUrl">ФИО</TableHeaderCell>
        <TableHeaderCell :icon="filterIconUrl">Дата рождения</TableHeaderCell>
        <TableHeaderCell :icon="filterIconUrl">Доп столбец</TableHeaderCell>
      </tr>
    </thead>

    <tbody>
      <template v-for="row in patientRows" :key="row.amb_card_num">
        <PatientRow
          :row="row"
          :is-open="openedAmb === row.amb_card_num"
          :cards="stacCardsByAmb[row.amb_card_num] || []"
          @toggle="togglePatient"
          @open-stac-card="emit('open-stac-card', $event)"
        />
      </template>

      <tr v-if="patientRows.length === 0">
        <td colspan="4" class="empty-cell">Нет данных</td>
      </tr>
    </tbody>
  </table>
</template>

<script setup>
import { ref, toRef } from 'vue'
import filterIconUrl from '@/assets/img/filter.svg'

import { useStacCardsByAmb } from '@/composables/useStacCardsByAmb'
import PatientRow from './PatientRow.vue'
import TableHeaderCell from './TableHeaderCell.vue'

const props = defineProps({
  patients: { type: Array, required: true }, // сейчас это список стац. карт
})

const emit = defineEmits(['open-stac-card'])

const openedAmb = ref(null)
function togglePatient(amb) {
  openedAmb.value = openedAmb.value === amb ? null : amb
}

const { stacCardsByAmb, patientRows } = useStacCardsByAmb(toRef(props, 'patients'))
</script>

<style scoped>
/* Верхняя таблица (пациенты) */
.patients-root-table th,
.patients-root-table td {
  white-space: nowrap;
}

.empty-cell {
  padding: 12px;
  opacity: 0.7;
}
</style>
