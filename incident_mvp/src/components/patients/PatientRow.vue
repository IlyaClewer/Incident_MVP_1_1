<template>
  <tr
    class="event-row patient-row"
    :class="{ 'event-row--selected': isOpen }"
    @click="emit('toggle', row.key)"
  >
    <td class="cell-center">
      <HighlightedText :text="row.amb_card_num" :query="searchQuery" />
    </td>
    <td>
      <HighlightedText :text="row.patientName" :query="searchQuery" />
    </td>
    <td class="cell-center">
      <HighlightedText :text="formattedBirthDate" :query="searchQuery" />
    </td>
    <td class="cell-center">
      <HighlightedText :text="row.departmentDisplay" :query="searchQuery" />
    </td>
  </tr>

  <tr v-if="isOpen" class="event-details-row">
    <td colspan="4">
      <div class="event-details-inner is-open stac-wrapper">
        <StacCardsTable
          :cards="cards"
          :search-query="searchQuery"
          @open-stac-card="emit('open-stac-card', $event)"
        />
      </div>
    </td>
  </tr>
</template>

<script setup>
import { computed } from 'vue'

import HighlightedText from '@/components/ui/HighlightedText.vue'
import { formatDate } from '@/utils/dateFormatter'

import StacCardsTable from './StacCardsTable.vue'

const props = defineProps({
  row: { type: Object, required: true },
  isOpen: { type: Boolean, required: true },
  cards: { type: Array, required: true },
  searchQuery: { type: String, default: '' },
})

const emit = defineEmits(['toggle', 'open-stac-card'])

const formattedBirthDate = computed(() => formatDate(props.row.birthDate))
</script>

<style scoped>
.patient-row {
  cursor: pointer;
}

.cell-center {
  text-align: center;
}

.event-details-row {
  position: relative;
  z-index: 80;
}

.stac-wrapper {
  border: none;
  box-shadow: none;
  background: transparent;
  max-height: none;
  overflow: visible;
  position: relative;
  z-index: 20;
}
</style>
