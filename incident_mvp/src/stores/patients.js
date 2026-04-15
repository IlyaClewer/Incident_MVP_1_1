import { defineStore } from 'pinia'

import { api } from '@/utils/api'
import { toDateInputValue } from '@/utils/dateFormatter'
import { getBestRecordMatch } from '@/utils/fuzzySearch'

const DEFAULT_PATIENT_FILTERS = () => ({
  ambCard: '',
  patientName: '',
  birthDate: '',
  departments: [],
})

const DEFAULT_STAC_FILTERS = () => ({
  departmentValues: [],
  dateHosp: '',
  dateOperation: '',
  dateDischarge: '',
  statuses: [],
})

const STATUS_OPTIONS = [
  { value: 'new', label: 'Новый' },
  { value: 'confirmed', label: 'Подтвержден' },
  { value: 'rejected', label: 'Отклонен' },
]

function formatStatusLabel(status) {
  switch (normalizeStatus(status)) {
    case 'confirmed':
      return 'Подтвержден'
    case 'rejected':
      return 'Отклонен'
    default:
      return 'Новый'
  }
}

function normalizeStatus(status) {
  switch (String(status ?? '').toLowerCase()) {
    case 'confirmed':
    case 'approved':
    case 'accepted':
      return 'confirmed'
    case 'rejected':
      return 'rejected'
    default:
      return 'new'
  }
}

function diagnosisStateKey(stacCardId, expertGroupId, diagnosisId) {
  return `${stacCardId}:${expertGroupId}:${diagnosisId}`
}

function flattenPatients(patients) {
  return (patients ?? []).flatMap((patient) =>
    (patient.stac_cards ?? []).map((card) => ({
      ...card,
      amb_card_num: card.amb_card_num ?? patient.amb_card_num ?? null,
      patientName: patient.patientName ?? null,
      birthDate: patient.birthDate ?? null,
    }))
  )
}

function buildDiagnosisStateIndex(diagnosisStates) {
  const index = {}

  for (const item of diagnosisStates ?? []) {
    index[
      diagnosisStateKey(item.stac_card_id, item.expert_group_id, item.diagnosis_id)
    ] = item
  }

  return index
}

function buildStacCardDiagnosisIndex(diagnosisStates, fallbackIndex) {
  const index = {}

  for (const item of diagnosisStates ?? []) {
    const key = String(item.stac_card_id)
    ;(index[key] ||= new Set()).add(item.diagnosis_id)
  }

  if (Object.keys(index).length > 0) {
    return Object.fromEntries(
      Object.entries(index).map(([key, value]) => [
        key,
        [...value].sort((left, right) => left - right),
      ])
    )
  }

  return Object.fromEntries(
    Object.entries(fallbackIndex ?? {}).map(([key, value]) => [
      String(key),
      [...new Set(value ?? [])].sort((left, right) => left - right),
    ])
  )
}

function collectDiagnosisCardIds(diagnosisId, diagnosisStates) {
  return [
    ...new Set(
      (diagnosisStates ?? [])
        .filter((item) => String(item.diagnosis_id) === String(diagnosisId))
        .map((item) => item.stac_card_id)
    ),
  ].sort((left, right) => left - right)
}

function normalizeDiagnosisState(item) {
  return {
    id: Number(item.id),
    stac_card_id: Number(item.stac_card_id),
    diagnosis_id: Number(item.diagnosis_id),
    expert_group_id: Number(item.expert_group_id),
    status: normalizeStatus(item.status),
  }
}

function aggregateCardStatus(cardId, diagnosisStates, fallbackStatus = 'new') {
  const statuses = new Set(
    (diagnosisStates ?? [])
      .filter((item) => String(item.stac_card_id) === String(cardId))
      .map((item) => normalizeStatus(item.status))
  )

  if (statuses.has('new')) return 'new'
  if (statuses.has('rejected')) return 'rejected'
  if (statuses.has('confirmed')) return 'confirmed'

  return normalizeStatus(fallbackStatus)
}

function syncCardStatuses(cards, diagnosisStates) {
  return (cards ?? []).map((card) => ({
    ...card,
    status: aggregateCardStatus(card.id, diagnosisStates, card.status),
  }))
}

function normalizeText(value) {
  return String(value ?? '')
    .trim()
    .toLowerCase()
    .replaceAll('ё', 'е')
}

function normalizeDepartmentValue(value) {
  const normalized = String(value ?? '').trim()
  return normalized || '—'
}

function sortNaturally(values) {
  return [...values].sort((left, right) =>
    String(left).localeCompare(String(right), 'ru', {
      numeric: true,
      sensitivity: 'base',
    })
  )
}

function matchesTextFilter(value, filterValue) {
  if (!filterValue) {
    return true
  }

  return normalizeText(value).includes(normalizeText(filterValue))
}

function matchesDateFilter(value, filterValue) {
  if (!filterValue) {
    return true
  }

  return toDateInputValue(value) === filterValue
}

function getCardsByAmb(cards) {
  return (cards ?? []).reduce((accumulator, card) => {
    const key = String(card.amb_card_num ?? `UNKNOWN-${card.id}`)
    ;(accumulator[key] ||= []).push(card)
    return accumulator
  }, {})
}

function getDepartmentsFromCards(cards) {
  const uniqueDepartments = new Set(
    (cards ?? [])
      .map((card) => normalizeDepartmentValue(card.department))
      .filter((value) => value !== '—')
  )

  return sortNaturally([...uniqueDepartments])
}

function patientMatchesFilters(entry, filters) {
  const selectedDepartments = new Set(filters.departments ?? [])

  if (!matchesTextFilter(entry.row.amb_card_num, filters.ambCard)) {
    return false
  }

  if (!matchesTextFilter(entry.row.patientName, filters.patientName)) {
    return false
  }

  if (!matchesDateFilter(entry.row.birthDate, filters.birthDate)) {
    return false
  }

  if (!selectedDepartments.size) {
    return true
  }

  return entry.row.departments.some((department) => selectedDepartments.has(department))
}

function stacCardMatchesFilters(card, filters) {
  const selectedDepartments = new Set(filters.departmentValues ?? [])
  const selectedStatuses = new Set(filters.statuses ?? [])

  if (selectedDepartments.size && !selectedDepartments.has(normalizeDepartmentValue(card.department))) {
    return false
  }

  if (selectedStatuses.size && !selectedStatuses.has(normalizeStatus(card.status))) {
    return false
  }

  if (!matchesDateFilter(card.date_hosp, filters.dateHosp)) {
    return false
  }

  if (!matchesDateFilter(card.date_operation, filters.dateOperation)) {
    return false
  }

  if (!matchesDateFilter(card.date_discharge, filters.dateDischarge)) {
    return false
  }

  return true
}

function getPatientSearchTexts(entry) {
  return [
    entry.row.amb_card_num,
    entry.row.patientName,
    entry.row.birthDate,
    entry.row.departmentDisplay,
  ]
}

function getCardSearchTexts(card) {
  return [
    card.cardNumber,
    normalizeDepartmentValue(card.department),
    normalizeStatus(card.status),
    formatStatusLabel(card.status),
    card.date_hosp,
    card.date_operation,
    card.date_discharge,
  ]
}

function enhanceEntriesWithSearch(query, entries) {
  const normalizedQuery = String(query ?? '').trim()
  if (!normalizedQuery) {
    return entries
  }

  return entries
    .map((entry, entryIndex) => {
      const patientMatch = getBestRecordMatch(normalizedQuery, getPatientSearchTexts(entry))
      const cardScores = entry.cards.map((card, cardIndex) => ({
        card,
        score: getBestRecordMatch(normalizedQuery, [
          ...getCardSearchTexts(card),
          entry.row.patientName,
          entry.row.amb_card_num,
        ]).score,
        order: cardIndex,
      }))

      const matchingCards =
        patientMatch.score > 0
          ? cardScores
          : cardScores.filter((item) => item.score > 0)

      if (!matchingCards.length && patientMatch.score <= 0) {
        return null
      }

      const sortedCards = matchingCards
        .sort(
          (left, right) =>
            right.score - left.score ||
            left.order - right.order
        )
        .map((item) => item.card)

      const topCardScore = matchingCards[0]?.score ?? 0
      const searchScore = Math.max(patientMatch.score, topCardScore)

      return {
        ...entry,
        cards: sortedCards,
        searchScore,
        order: entryIndex,
      }
    })
    .filter(Boolean)
    .sort(
      (left, right) =>
        right.searchScore - left.searchScore ||
        left.order - right.order
    )
}

export const usePatientsStore = defineStore('patients', {
  state: () => ({
    patients: [],
    stacCards: [],
    expertGroups: [],
    diagnoses: [],
    diagnosisStates: [],
    diagnosisStateIndex: {},
    stacCardDiagnosisIndex: {},
    eventsByCardId: {},
    eventsLoadingByCardId: {},
    selectedExpertGroupId: 'all',
    selectedDiagnosisIds: [],
    searchDraft: '',
    searchQuery: '',
    patientFilters: DEFAULT_PATIENT_FILTERS(),
    stacFilters: DEFAULT_STAC_FILTERS(),
    isBootstrapping: false,
    isLoadingPatients: false,
    isLoadingMeta: false,
    isUpdatingDiagnosisState: false,
    isTransferringDiagnosisEvents: false,
    bootstrapError: '',
  }),

  getters: {
    getStacCardById: (state) => (id) =>
      state.stacCards.find((card) => String(card.id) === String(id)),

    getEventsForCard: (state) => (id) =>
      state.eventsByCardId[String(id)] ?? [],

    getDiagnosisState: (state) => (stacCardId, groupId, diagnosisId) =>
      state.diagnosisStateIndex[
        diagnosisStateKey(stacCardId, groupId, diagnosisId)
      ] ?? null,

    filteredDiagnosesNonEmpty(state) {
      return (state.diagnoses ?? []).filter(
        (diagnosis) => (diagnosis?.stac_card_ids?.length ?? 0) > 0
      )
    },

    availableDiagnosesForFilter() {
      if (!this.selectedExpertGroupId || this.selectedExpertGroupId === 'all') {
        return this.filteredDiagnosesNonEmpty
      }

      const group = (this.expertGroups ?? []).find(
        (item) => String(item.id) === String(this.selectedExpertGroupId)
      )
      const allowed = new Set(group?.diagnosis_ids ?? [])

      return this.filteredDiagnosesNonEmpty.filter((diagnosis) =>
        allowed.has(diagnosis.id)
      )
    },

    patientDepartmentOptions(state) {
      const values = new Set(
        (state.stacCards ?? [])
          .map((card) => normalizeDepartmentValue(card.department))
          .filter((value) => value !== '—')
      )

      return sortNaturally([...values])
    },

    stacDepartmentOptions() {
      return this.patientDepartmentOptions
    },

    stacStatusOptions(state) {
      const presentStatuses = new Set(
        (state.stacCards ?? []).map((card) => normalizeStatus(card.status))
      )

      return STATUS_OPTIONS.filter(
        (option) => !presentStatuses.size || presentStatuses.has(option.value)
      )
    },

    diagnosisFilteredStacCards(state) {
      let cards = state.stacCards.filter(
        (card) => (state.stacCardDiagnosisIndex[String(card.id)] ?? []).length > 0
      )

      if (state.selectedExpertGroupId && state.selectedExpertGroupId !== 'all') {
        cards = cards.filter((card) =>
          state.diagnosisStates.some(
            (item) =>
              String(item.stac_card_id) === String(card.id) &&
              String(item.expert_group_id) === String(state.selectedExpertGroupId)
          )
        )
      }

      if (state.selectedDiagnosisIds.length > 0) {
        const selected = new Set(state.selectedDiagnosisIds.map(Number))
        cards = cards.filter((card) =>
          (state.stacCardDiagnosisIndex[String(card.id)] ?? []).some((diagnosisId) =>
            selected.has(Number(diagnosisId))
          )
        )
      }

      return cards
    },

    filteredTableEntries() {
      const diagnosisFilteredCardsByAmb = getCardsByAmb(this.diagnosisFilteredStacCards)

      const patientLevelEntries = (this.patients ?? [])
        .map((patient, patientIndex) => {
          const ambKey = String(
            patient.amb_card_num ??
              patient.stac_cards?.[0]?.amb_card_num ??
              `UNKNOWN-${patientIndex}`
          )
          const baseCards = diagnosisFilteredCardsByAmb[ambKey] ?? []
          if (!baseCards.length) {
            return null
          }

          const departments = getDepartmentsFromCards(baseCards)

          return {
            row: {
              key: ambKey,
              amb_card_num: patient.amb_card_num ?? '—',
              patientName: patient.patientName ?? '—',
              birthDate: patient.birthDate ?? '',
              departments,
              departmentDisplay: departments.join(', ') || '—',
            },
            cards: baseCards,
          }
        })
        .filter(Boolean)
        .filter((entry) => patientMatchesFilters(entry, this.patientFilters))

      const stacLevelEntries = patientLevelEntries
        .map((entry) => ({
          ...entry,
          cards: entry.cards.filter((card) => stacCardMatchesFilters(card, this.stacFilters)),
        }))
        .filter((entry) => entry.cards.length > 0)

      return enhanceEntriesWithSearch(this.searchQuery, stacLevelEntries)
    },

    filteredStacCards() {
      return this.filteredTableEntries.flatMap((entry) => entry.cards)
    },

    stacCardsByAmb() {
      return Object.fromEntries(
        this.filteredTableEntries.map((entry) => [entry.row.key, entry.cards])
      )
    },

    filteredPatientRows() {
      return this.filteredTableEntries.map((entry) => entry.row)
    },

    diagnosesForCardInGroup: (state) => (stacCardId, groupId) => {
      const relevantStates = (state.diagnosisStates ?? [])
        .filter(
          (item) =>
            String(item.stac_card_id) === String(stacCardId) &&
            (groupId === 'all' || String(item.expert_group_id) === String(groupId))
        )
        .sort((left, right) => left.diagnosis_id - right.diagnosis_id)

      return relevantStates
        .map((item) => {
          const diagnosis = (state.diagnoses ?? []).find(
            (entry) => String(entry.id) === String(item.diagnosis_id)
          )

          if (!diagnosis) {
            return null
          }

          return {
            ...diagnosis,
            diagnosisStateId: item.id,
            status: item.status,
            expert_group_id: item.expert_group_id,
          }
        })
        .filter(Boolean)
    },
  },

  actions: {
    async bootstrap() {
      if (this.isBootstrapping) {
        return
      }

      this.isBootstrapping = true
      this.bootstrapError = ''

      try {
        await Promise.all([this.fetchPatients(), this.fetchMeta()])
      } catch (error) {
        this.bootstrapError =
          error instanceof Error ? error.message : 'Не удалось загрузить данные'
        throw error
      } finally {
        this.isBootstrapping = false
      }
    },

    async fetchPatients() {
      if (this.isLoadingPatients) {
        return
      }

      this.isLoadingPatients = true

      try {
        const payload = await api.getPatients()
        this.patients = payload?.patients ?? []
        this.stacCards = syncCardStatuses(
          flattenPatients(this.patients),
          this.diagnosisStates
        )
      } finally {
        this.isLoadingPatients = false
      }
    },

    async fetchMeta() {
      if (this.isLoadingMeta) {
        return
      }

      this.isLoadingMeta = true

      try {
        const meta = await api.getMeta()
        const diagnosisStates = (meta?.diagnosis_states ?? []).map(normalizeDiagnosisState)

        this.expertGroups = [
          { id: 'all', title: 'Все', diagnosis_ids: [] },
          ...(meta?.expert_groups ?? []),
        ]
        this.diagnosisStates = diagnosisStates
        this.diagnosisStateIndex = buildDiagnosisStateIndex(diagnosisStates)
        this.stacCardDiagnosisIndex = buildStacCardDiagnosisIndex(
          diagnosisStates,
          meta?.stac_card_diagnosis_index
        )
        this.diagnoses = (meta?.diagnoses ?? []).map((diagnosis) => ({
          ...diagnosis,
          stac_card_ids:
            (diagnosis?.stac_card_ids?.length ?? 0) > 0
              ? diagnosis.stac_card_ids
              : collectDiagnosisCardIds(diagnosis.id, diagnosisStates),
          event_type_ids: diagnosis?.event_type_ids ?? [],
          formulas: diagnosis?.formulas ?? [],
        }))
        this.stacCards = syncCardStatuses(this.stacCards, diagnosisStates)

        if (!this.selectedExpertGroupId) {
          this.selectedExpertGroupId = 'all'
        }
      } finally {
        this.isLoadingMeta = false
      }
    },

    async fetchEventsForCard(stacCardId, force = false) {
      const key = String(stacCardId)

      if (!force && this.eventsByCardId[key]) {
        return this.eventsByCardId[key]
      }

      if (this.eventsLoadingByCardId[key]) {
        return this.eventsByCardId[key] ?? []
      }

      this.eventsLoadingByCardId = {
        ...this.eventsLoadingByCardId,
        [key]: true,
      }

      try {
        const payload = await api.getStacCardEvents(stacCardId)
        this.eventsByCardId = {
          ...this.eventsByCardId,
          [key]: payload?.events ?? [],
        }
        return this.eventsByCardId[key]
      } finally {
        this.eventsLoadingByCardId = {
          ...this.eventsLoadingByCardId,
          [key]: false,
        }
      }
    },

    async updateDiagnosisState(diagnosisStateId, payload) {
      this.isUpdatingDiagnosisState = true

      try {
        const response = await api.updateDiagnosisState(diagnosisStateId, payload)
        const updated = normalizeDiagnosisState(response?.diagnosis_state ?? {})
        const nextDiagnosisStates = (this.diagnosisStates ?? [])
          .filter((item) => item.id !== updated.id)
          .concat(updated)
          .sort(
            (left, right) =>
              left.stac_card_id - right.stac_card_id ||
              left.expert_group_id - right.expert_group_id ||
              left.diagnosis_id - right.diagnosis_id
          )

        this.diagnosisStates = nextDiagnosisStates
        this.diagnosisStateIndex = buildDiagnosisStateIndex(nextDiagnosisStates)
        this.stacCardDiagnosisIndex = buildStacCardDiagnosisIndex(
          nextDiagnosisStates,
          this.stacCardDiagnosisIndex
        )
        this.stacCards = syncCardStatuses(this.stacCards, nextDiagnosisStates)

        return updated
      } finally {
        this.isUpdatingDiagnosisState = false
      }
    },

    async transferDiagnosisEvents(diagnosisStateId, payload, options = {}) {
      this.isTransferringDiagnosisEvents = true

      try {
        const response = await api.transferDiagnosisEvents(diagnosisStateId, payload)
        const resolvedStacCardId =
          options?.stacCardId ??
          this.diagnosisStates.find(
            (item) => String(item.id) === String(diagnosisStateId)
          )?.stac_card_id

        if (resolvedStacCardId != null) {
          await this.fetchEventsForCard(resolvedStacCardId, true)
        }

        return response
      } finally {
        this.isTransferringDiagnosisEvents = false
      }
    },

    setExpertGroup(id) {
      this.selectedExpertGroupId = id
      this.selectedDiagnosisIds = []
    },

    setSelectedDiagnosisIds(ids) {
      this.selectedDiagnosisIds = Array.isArray(ids)
        ? ids.map(Number).filter((value) => Number.isFinite(value))
        : []
    },

    setSearchDraft(value) {
      this.searchDraft = String(value ?? '')
    },

    applySearchQuery(value = this.searchDraft) {
      const nextValue = String(value ?? '')
      this.searchDraft = nextValue
      this.searchQuery = nextValue
    },

    resetSearchQuery() {
      this.searchDraft = ''
      this.searchQuery = ''
    },

    resetAllFilters() {
      this.selectedExpertGroupId = 'all'
      this.selectedDiagnosisIds = []
      this.searchDraft = ''
      this.searchQuery = ''
      this.patientFilters = DEFAULT_PATIENT_FILTERS()
      this.stacFilters = DEFAULT_STAC_FILTERS()
    },

    setPatientFilter(key, value) {
      this.patientFilters = {
        ...this.patientFilters,
        [key]: Array.isArray(value) ? [...value] : String(value ?? ''),
      }
    },

    setStacFilter(key, value) {
      this.stacFilters = {
        ...this.stacFilters,
        [key]: Array.isArray(value) ? [...value] : String(value ?? ''),
      }
    },
  },
})
