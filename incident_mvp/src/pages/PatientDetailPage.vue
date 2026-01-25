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
        <PatientSummaryCard :card="card" />

        <StacCardsStrip
          :cards="displayedStacCards"
          :active-id="id"
          :placeholders-count="placeholdersCount"
          @select="openStacCard"
        />
      </div>

      <div class="events-panel">
        <EventsToolbar
          :groups="expertGroupsForToolbar"
          :active="activeExpertGroupId"
          @update:active="onSelectGroup"
          :diagnoses="diagnosisTabTitles"
          :active-diagnosis="activeDiagnosisTitle"
          @update:activeDiagnosis="onSelectDiagnosisTitle"
        />

        <StacEventsTable :events="displayedEvents" />
      </div>

      <p class="patient-hint">
        Здесь позже будет: события пациента, фильтры по стац. карте, вкладки экспертных групп.
      </p>
    </template>
  </main>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { toRef } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { usePatientsStore } from '@/stores/patients'
import { useDisplayedStacCards } from '@/composables/useDisplayedStacCards'

import PatientTopbar from '@/components/patient-detail/PatientTopbar.vue'
import PatientSummaryCard from '@/components/patient-detail/PatientSummaryCard.vue'
import StacCardsStrip from '@/components/patient-detail/StacCardsStrip.vue'
import EventsToolbar from '@/components/patient-detail/EventsToolbar.vue'
import StacEventsTable from '@/components/patient-detail/StacEventsTable.vue'

const PROCHOE_ID = '__other__'
const PROCHOE_TITLE = 'Прочее'

const props = defineProps({
  id: { type: String, required: true },
})

const router = useRouter()
const route = useRoute()
const store = usePatientsStore()

const card = computed(() => store.getById(props.id))
const allCardEvents = computed(() => card.value?.events ?? [])

const { displayedStacCards, placeholdersCount } = useDisplayedStacCards(
  toRef(() => store.patients),
  card,
  3
)

// ====== группы: только те, что применимы к карте ======
const availableExpertGroupsForCard = computed(() => {
  if (!card.value) return []

  const cardDxIds = new Set(store.stacCardDiagnosisIndex?.[String(card.value.id)] ?? [])
  if (cardDxIds.size === 0) return []

  return (store.expertGroups ?? [])
    .filter(g => g.id !== 'all')
    .filter(g => (g.diagnosis_ids ?? []).some(dxId => cardDxIds.has(dxId)))
})

const expertGroupsForToolbar = computed(() => {
  const list = availableExpertGroupsForCard.value.map(g => ({ id: g.id, title: g.title }))
  return list.length ? list : [{ id: 'all', title: 'Без диагнозов' }]
})

const activeExpertGroupId = ref('all')

// ====== диагнозы для текущей карты в текущей группе ======
const cardDiagnosesInGroup = computed(() => {
  if (!card.value) return []
  return store.diagnosesForCardInGroup(card.value.id, activeExpertGroupId.value) ?? []
})

const diagnosisTabTitles = computed(() => {
  const titles = cardDiagnosesInGroup.value.map(d => d.name)
  titles.push(PROCHOE_TITLE)
  return titles
})

const diagnosisIdByTitle = computed(() => {
  const map = {}
  for (const d of cardDiagnosesInGroup.value) map[d.name] = d.id
  map[PROCHOE_TITLE] = PROCHOE_ID
  return map
})

const activeDiagnosisTitle = ref(PROCHOE_TITLE)
const activeDiagnosisId = computed(() => diagnosisIdByTitle.value[activeDiagnosisTitle.value] ?? PROCHOE_ID)

// ====== события по диагнозу ======
const eventsForDiagnosisId = computed(() => {
  const dxId = activeDiagnosisId.value
  if (!card.value) return []
  if (dxId === PROCHOE_ID) return []

  const required = new Set(store.dxEventIdsIndex?.[dxId] ?? [])
  if (required.size === 0) return []

  return allCardEvents.value.filter(ev => {
    const ids = ev?.event_ids ?? []
    return ids.some(x => required.has(Number(x)))
  })
})

const otherEvents = computed(() => {
  if (!card.value) return []

  const coveredEventKeys = new Set()
  for (const dx of cardDiagnosesInGroup.value) {
    const required = new Set(store.dxEventIdsIndex?.[dx.id] ?? [])
    if (required.size === 0) continue

    for (const ev of allCardEvents.value) {
      const ids = ev?.event_ids ?? []
      if (ids.some(x => required.has(Number(x)))) {
        coveredEventKeys.add(String(ev.id))
      }
    }
  }

  return allCardEvents.value.filter(ev => !coveredEventKeys.has(String(ev.id)))
})

const displayedEvents = computed(() => {
  return activeDiagnosisId.value === PROCHOE_ID
    ? otherEvents.value
    : eventsForDiagnosisId.value
})

// ====== init из query ======
function initFromQuery() {
  const qg = route.query.g ? String(route.query.g) : null
  const qdx = route.query.dx ? String(route.query.dx) : null

  const availableIds = new Set(expertGroupsForToolbar.value.map(g => g.id))

  activeExpertGroupId.value = (qg && availableIds.has(qg))
    ? qg
    : (expertGroupsForToolbar.value[0]?.id ?? 'all')

  if (qdx) {
    const found = cardDiagnosesInGroup.value.find(d => d.id === qdx)
    activeDiagnosisTitle.value = found?.name ?? PROCHOE_TITLE
  } else {
    activeDiagnosisTitle.value = cardDiagnosesInGroup.value[0]?.name ?? PROCHOE_TITLE
  }
}

watch(
  () => [card.value?.id, store.expertGroups.length, store.diagnoses.length],
  () => {
    if (!card.value) return
    initFromQuery()
  },
  { immediate: true }
)

function onSelectGroup(groupId) {
  activeExpertGroupId.value = groupId
  activeDiagnosisTitle.value = cardDiagnosesInGroup.value[0]?.name ?? PROCHOE_TITLE

  router.replace({
    query: {
      ...route.query,
      g: groupId,
      dx: activeDiagnosisId.value === PROCHOE_ID ? undefined : activeDiagnosisId.value,
    }
  })
}

function onSelectDiagnosisTitle(title) {
  activeDiagnosisTitle.value = title
  const dxId = diagnosisIdByTitle.value[title]

  router.replace({
    query: {
      ...route.query,
      g: activeExpertGroupId.value,
      dx: dxId === PROCHOE_ID ? undefined : dxId,
    }
  })
}

function goBack() {
  router.push({ name: 'patients' })
}

function openStacCard(stacCardId) {
  router.push({
    name: 'patient',
    params: { id: String(stacCardId) },
    query: {
      g: activeExpertGroupId.value,
      dx: activeDiagnosisId.value === PROCHOE_ID ? undefined : activeDiagnosisId.value,
    },
  })
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

.cards-row {
  display: grid;
  grid-template-columns: 460px 1fr;
  align-items: start;
  gap: 60px;
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
  overflow: hidden;
}
.events-panel :deep(.events-table thead) {
  position: static;
}
</style>
