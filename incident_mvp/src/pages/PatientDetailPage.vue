<template>
  <PatientTopbar :card-number="card?.cardNumber ?? ''" @back="goBack" />

  <main class="page-container">
    <div v-if="!card" class="error-message">
      Стац. карта не найдена (id: {{ id }})
    </div>

    <template v-else>
      <div class="patient-head">
        <div>
          <h2 class="patient-name">{{ card.patientName ?? '—' }}</h2>
          <div class="patient-ids">
            <span class="pill">Амб. карта: {{ card.amb_card_num ?? '—' }}</span>
            <span class="pill">Стац. карта: {{ card.cardNumber ?? '—' }}</span>
          </div>
        </div>
      </div>
      <div class="cards-row">
        <PatientSummaryCard
          :card="card"
        />

        <StacCardsStrip
          :cards="displayedStacCards"
          :active-id="id"
          :placeholders-count="placeholdersCount"
          @select="openStacCard"
        />
      </div>

      <div class="events-panel">
        <EventsToolbar
            :groups="expertGroups"
            :active="activeExpertGroup"
            @update:active="activeExpertGroup = $event"
            :diagnoses="diagnosisTabs"
            :active-diagnosis="activeDiagnosis"
            @update:activeDiagnosis="activeDiagnosis = $event"
          />

        <StacEventsTable :events="stacEvents" />
      </div>


      <p class="patient-hint">
        Здесь позже будет: события пациента, фильтры по стац. карте, вкладки экспертных групп.
      </p>
    </template>
  </main>
</template>

<script setup>
import { computed, ref } from 'vue'
import { toRef } from 'vue'
import { useRouter } from 'vue-router'
import { usePatientsStore } from '@/stores/patients'
import { useDisplayedStacCards } from '@/composables/useDisplayedStacCards'

import PatientTopbar from '@/components/patient-detail/PatientTopbar.vue'
import PatientSummaryCard from '@/components/patient-detail/PatientSummaryCard.vue'
import StacCardsStrip from '@/components/patient-detail/StacCardsStrip.vue'
import EventsToolbar from '@/components/patient-detail/EventsToolbar.vue'
import StacEventsTable from '@/components/patient-detail/StacEventsTable.vue'

const props = defineProps({
  id: { type: String, required: true },
})

const router = useRouter()
const store = usePatientsStore()

const card = computed(() => store.getById(props.id))

// const mockEvents = computed(() => {
//   if (!card.value) return []
//   return Array.from({ length: 3 }, () => ({
//     date_trigger: card.value.date_trigger ?? '—',
//     trigger: card.value.trigger ?? '—',
//   }))
// })
const stacEvents = computed(() => card.value?.events ?? [])

const expertGroups = ['Эксп. группа A', 'Эксп. группа B', 'Эксп. группа C', 'Эксп. группа D', 'Эксп. группа E']
const activeExpertGroup = ref(expertGroups[0])

const { displayedStacCards, placeholdersCount } = useDisplayedStacCards(toRef(() => store.patients), card, 3)

const diagnosisTabs = [
  'Диагноз A',
  'Диагноз B',
  'Диагноз C',
  'Диагноз D',
]

const activeDiagnosis = ref(diagnosisTabs[0])

function goBack() {
  router.push({ name: 'patients' })
}

function openStacCard(stacCardId) {
  router.push({ name: 'patient', params: { id: String(stacCardId) } })
}
</script>

<style scoped>
.patient-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;
}

.patient-name {
  margin: 0 0 6px 0;
}

.patient-ids {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  opacity: 0.95;
}

.pill {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  background: #eef2ff;
  border: 1px solid #c7d2fe;
  font-size: 12.5px;
}

/* “таблица” в одну строку */
.cards-row {
  display: grid;
  grid-template-columns: 460px 1fr;
  align-items: start;
  gap: 60px;            /* было 25px */
  margin: 10px 0 55px 0;
}

@media (max-width: 1200px) {
  .cards-row {
    grid-template-columns: 1fr;
    gap: 12px;
  }
}

.patient-hint {
  opacity: 0.7;
  font-size: 13px;
  margin-top: 10px;
}

.events-panel {
  border: 1px solid #c6ccde;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.85);
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.12);
  overflow: hidden; /* чтобы углы таблицы/шапки были “одним блоком” */
}
.events-panel :deep(.events-table thead) {
  position: static;
}

</style>

