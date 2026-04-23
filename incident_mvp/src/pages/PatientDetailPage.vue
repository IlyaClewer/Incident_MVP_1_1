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
          :diagnoses="diagnosisTabTitles"
          :active-diagnosis="activeDiagnosisTitle"
          :model-probability="modelProbabilityPlaceholder"
          :stac-card-id="card?.id ?? null"
          :diagnosis-state-id="activeDiagnosis?.diagnosisStateId ?? null"
          :diagnosis-status="activeDiagnosis?.status ?? ''"
          :selected-event-ids="selectedEventIds"
          :transfer-target-diagnoses="transferTargetDiagnoses"
          @update:active="onSelectGroup"
          @update:activeDiagnosis="onSelectDiagnosisTitle"
          @transfer-complete="clearSelectedEvents"
        />

        <StacEventsTable
          :events="displayedEvents"
          :diagnosis="activeDiagnosis"
          :selected-event-ids="selectedEventIds"
          :selection-enabled="Boolean(activeDiagnosis?.diagnosisStateId)"
          @update:selectedEventIds="onSelectedEventIdsChange"
        />
      </div>
    </template>
  </main>
</template>

<script setup>
import { computed, ref, toRef, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import EventsToolbar from '@/components/patient-detail/EventsToolbar.vue'
import PatientSummaryCard from '@/components/patient-detail/PatientSummaryCard.vue'
import PatientTopbar from '@/components/patient-detail/PatientTopbar.vue'
import StacCardsStrip from '@/components/patient-detail/StacCardsStrip.vue'
import StacEventsTable from '@/components/patient-detail/StacEventsTable.vue'
import { useDisplayedStacCards } from '@/composables/useDisplayedStacCards'
import { usePatientsStore } from '@/stores/patients'

const OTHER_ID = '__other__'
const OTHER_TITLE = 'Прочее'

const props = defineProps({
  id: { type: String, required: true },
})

const router = useRouter()
const route = useRoute()
const store = usePatientsStore()

const card = computed(() => store.getStacCardById(props.id))
const allCardEvents = computed(() => store.getEventsForCard(props.id))

const { displayedStacCards, placeholdersCount } = useDisplayedStacCards(
  toRef(() => store.stacCards),
  card,
  3
)

const availableExpertGroupsForCard = computed(() => {
  if (!card.value) {
    return []
  }

  const groupIds = new Set(
    (store.diagnosisStates ?? [])
      .filter((item) => String(item.stac_card_id) === String(card.value.id))
      .map((item) => String(item.expert_group_id))
  )

  return (store.expertGroups ?? [])
    .filter((group) => group.id !== 'all')
    .filter((group) => groupIds.has(String(group.id)))
})

const expertGroupsForToolbar = computed(() => {
  const list = availableExpertGroupsForCard.value.map((group) => ({
    id: group.id,
    title: group.title,
    group_diagnosis_ids: group.group_diagnosis_ids ?? [],
    primary_group_diagnosis_id: group.primary_group_diagnosis_id ?? null,
  }))

  return list.length > 0 ? list : [{ id: 'all', title: 'Без диагнозов' }]
})

const activeExpertGroupId = ref('all')
const selectedEventIds = ref([])

const activeExpertGroup = computed(
  () =>
    expertGroupsForToolbar.value.find(
      (group) => String(group.id) === String(activeExpertGroupId.value)
    ) ?? null
)

const activeExpertGroupDiagnosisGroupIds = computed(() => {
  if (!activeExpertGroup.value || String(activeExpertGroup.value.id) === 'all') {
    return []
  }

  return [
    activeExpertGroup.value.primary_group_diagnosis_id,
    ...(activeExpertGroup.value.group_diagnosis_ids ?? []),
  ]
    .map((value) => Number(value))
    .filter((value) => Number.isFinite(value))
})

const modelProbabilityPlaceholder = computed(() => {
  if (!card.value || activeExpertGroupDiagnosisGroupIds.value.length === 0) {
    return null
  }

  const visibleGroupDiagnosisIds = new Set(activeExpertGroupDiagnosisGroupIds.value)
  const modelResult = store
    .getModelResultsForCard(card.value.id)
    .filter(
      (item) =>
        item.has_complication &&
        item.group_diagnosis_id != null &&
        visibleGroupDiagnosisIds.has(Number(item.group_diagnosis_id))
    )
    .sort((left, right) => (right.probability ?? 0) - (left.probability ?? 0))[0]

  if (!modelResult) {
    return null
  }

  const probability = Number(modelResult.probability)
  const percent = Number.isFinite(probability)
    ? Math.round(probability <= 1 ? probability * 100 : probability)
    : null
  const diagnosisGroup = (store.groupDiagnoses ?? []).find(
    (item) => String(item.id) === String(modelResult.group_diagnosis_id)
  )

  return {
    title:
      modelResult.group_diagnosis_title ||
      diagnosisGroup?.title ||
      'Группа диагнозов не задана',
    percent: percent ?? 0,
  }
})

const cardDiagnosesInGroup = computed(() => {
  if (!card.value) {
    return []
  }

  return store.diagnosesForCardInGroup(card.value.id, activeExpertGroupId.value)
})

const diagnosisTabTitles = computed(() => [
  ...cardDiagnosesInGroup.value.map((diagnosis) => diagnosis.name),
  OTHER_TITLE,
])

const diagnosisIdByTitle = computed(() => {
  const map = {}

  for (const diagnosis of cardDiagnosesInGroup.value) {
    map[diagnosis.name] = diagnosis.id
  }

  map[OTHER_TITLE] = OTHER_ID

  return map
})

const activeDiagnosisTitle = ref(OTHER_TITLE)

const activeDiagnosisId = computed(
  () => diagnosisIdByTitle.value[activeDiagnosisTitle.value] ?? OTHER_ID
)

const activeDiagnosis = computed(() => {
  if (activeDiagnosisId.value === OTHER_ID) {
    return null
  }

  const diagnosis = cardDiagnosesInGroup.value.find(
    (item) => String(item.id) === String(activeDiagnosisId.value)
  )

  if (!diagnosis) {
    return null
  }

  return {
    ...diagnosis,
    title: diagnosis.name,
    description: diagnosis.description?.trim() ?? '',
  }
})

const transferTargetDiagnoses = computed(() => {
  if (!activeDiagnosis.value?.diagnosisStateId) {
    return []
  }

  return cardDiagnosesInGroup.value
    .filter(
      (diagnosis) =>
        String(diagnosis.diagnosisStateId) !==
        String(activeDiagnosis.value.diagnosisStateId)
    )
    .map((diagnosis) => ({
      ...diagnosis,
      title: diagnosis.name,
    }))
})

const displayedEvents = computed(() => {
  if (!card.value) {
    return []
  }

  if (!activeDiagnosis.value?.diagnosisStateId) {
    const visibleDiagnosisStateIds = new Set(
      cardDiagnosesInGroup.value.map((diagnosis) => diagnosis.diagnosisStateId)
    )

    return allCardEvents.value.filter(
      (event) =>
        !(event?.diagnosis_state_ids ?? []).some((id) =>
          visibleDiagnosisStateIds.has(id)
        )
    )
  }

  return allCardEvents.value.filter((event) =>
    (event?.diagnosis_state_ids ?? []).includes(activeDiagnosis.value.diagnosisStateId)
  )
})

function initFromQuery() {
  const queryGroupId = route.query.g ? String(route.query.g) : null
  const queryDiagnosisId = route.query.dx ? String(route.query.dx) : null

  const availableGroupIds = new Set(
    expertGroupsForToolbar.value.map((group) => String(group.id))
  )

  activeExpertGroupId.value =
    queryGroupId && availableGroupIds.has(queryGroupId)
      ? queryGroupId
      : String(expertGroupsForToolbar.value[0]?.id ?? 'all')

  if (queryDiagnosisId) {
    const match = cardDiagnosesInGroup.value.find(
      (diagnosis) => String(diagnosis.id) === queryDiagnosisId
    )
    activeDiagnosisTitle.value = match?.name ?? OTHER_TITLE
    return
  }

  activeDiagnosisTitle.value =
    cardDiagnosesInGroup.value[0]?.name ?? OTHER_TITLE
}

watch(
  () => props.id,
  async (nextId) => {
    if (!nextId) {
      return
    }

    try {
      await store.fetchEventsForCard(nextId)
    } catch (error) {
      console.error(error)
    }
  },
  { immediate: true }
)

watch(
  () => [card.value?.id, store.diagnosisStates.length, store.expertGroups.length],
  () => {
    if (!card.value) {
      return
    }

    initFromQuery()
  },
  { immediate: true }
)

watch(
  () => [props.id, activeExpertGroupId.value, activeDiagnosisTitle.value],
  () => {
    clearSelectedEvents()
  }
)

watch(
  displayedEvents,
  (events) => {
    const visibleEventIds = new Set(
      (events ?? []).map((event) => Number(event.id))
    )

    selectedEventIds.value = selectedEventIds.value.filter((eventId) =>
      visibleEventIds.has(Number(eventId))
    )
  },
  { immediate: true }
)

function onSelectGroup(groupId) {
  activeExpertGroupId.value = groupId
  activeDiagnosisTitle.value = cardDiagnosesInGroup.value[0]?.name ?? OTHER_TITLE

  router.replace({
    query: {
      ...route.query,
      g: groupId,
      dx:
        activeDiagnosisId.value === OTHER_ID
          ? undefined
          : activeDiagnosisId.value,
    },
  })
}

function onSelectDiagnosisTitle(title) {
  activeDiagnosisTitle.value = title
  const diagnosisId = diagnosisIdByTitle.value[title]

  router.replace({
    query: {
      ...route.query,
      g: activeExpertGroupId.value,
      dx: diagnosisId === OTHER_ID ? undefined : diagnosisId,
    },
  })
}

function onSelectedEventIdsChange(ids) {
  selectedEventIds.value = Array.isArray(ids)
    ? [...new Set(ids.map(Number).filter((value) => Number.isFinite(value)))]
    : []
}

function clearSelectedEvents() {
  selectedEventIds.value = []
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
      dx:
        activeDiagnosisId.value === OTHER_ID
          ? undefined
          : activeDiagnosisId.value,
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
