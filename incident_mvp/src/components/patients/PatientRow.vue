<template>
  <tr
    class="event-row patient-row"
    :class="{ 'event-row--selected': isOpen }"
    @click="emit('toggle', row.amb_card_num)"
  >
    <td class="cell-center">{{ row.amb_card_num ?? '—' }}</td>
    <td>{{ row.patientName ?? '—' }}</td>
    <td class="cell-center">{{ row.birthDate ?? row.patient_birthday ?? '—' }}</td>
    <td class="cell-center">{{ row.extra }}</td>
  </tr>

  <tr v-if="isOpen" class="event-details-row">
    <td colspan="4">
      <div class="event-details-inner is-open stac-wrapper">
        <StacCardsTable :cards="cards" @open-stac-card="emit('open-stac-card', $event)" />
      </div>
    </td>
  </tr>
</template>

<script setup>
import StacCardsTable from './StacCardsTable.vue'

defineProps({
  row: { type: Object, required: true },
  isOpen: { type: Boolean, required: true },
  cards: { type: Array, required: true },
})

const emit = defineEmits(['toggle', 'open-stac-card'])
</script>

<style scoped>
.patient-row {
  cursor: pointer;
}

.cell-center {
  text-align: center;
}

/* как ты решил — без внешней “обводки” вокруг блока вложенной таблицы */
.stac-wrapper {
  border: none;
  box-shadow: none;
  background: transparent;
}
</style>
