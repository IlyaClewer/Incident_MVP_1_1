// src/stores/patients.js
import { defineStore } from 'pinia'

// helper: делает из нового JSON плоский список стац-карт
function flattenToStacCards(data) {
  const patientsArr = Array.isArray(data) ? data : (data?.patients ?? [])

  return patientsArr.flatMap(p =>
    (p.stac_cards ?? []).map(c => ({
      ...c,
      amb_card_num: c.amb_card_num ?? p.amb_card_num,
      patientName: c.patientName ?? p.patientName,
      birthDate: c.birthDate ?? p.birthDate,
      patient_birthday: c.patient_birthday ?? p.birthDate,
    }))
  )
}

export const usePatientsStore = defineStore('patients', {
  state: () => ({
    patients: [], // плоский список стац-карт
    isLoading: false,

    // meta:
    expertGroups: [],
    diagnoses: [],
    stacCardDiagnosisIndex: {}, // { [stac_card_id]: [diagnosis_id,...] }

    // filters
    selectedExpertGroupId: null,
    selectedDiagnosisIds: [], // мультивыбор диагнозов
  }),

  getters: {
    getById: (state) => (id) =>
      state.patients.find(p => String(p.id) === String(id)),

    // Диагнозы, которые показываем в дропдауне (зависит от выбранной группы)
    availableDiagnosesForFilter: (state) => {
      // "Все" (или null) => показываем все диагнозы
      if (!state.selectedExpertGroupId || state.selectedExpertGroupId === 'all') {
        return state.diagnoses ?? []
      }

      const g = (state.expertGroups ?? []).find(x => x.id === state.selectedExpertGroupId)
      const allowed = new Set(g?.diagnosis_ids ?? [])
      return (state.diagnoses ?? []).filter(d => allowed.has(d.id))
    },

    filteredStacCards: (state) => {
      // 0) базовый фильтр: берём только карты с событиями
      let cards = state.patients.filter(c => (c.events?.length ?? 0) > 0)

      // 1) фильтр по экспертной группе
      if (state.selectedExpertGroupId && state.selectedExpertGroupId !== 'all') {
        const g = state.expertGroups.find(x => x.id === state.selectedExpertGroupId)
        const groupDxIds = new Set(g?.diagnosis_ids ?? [])

        if (groupDxIds.size === 0) return []

        cards = cards.filter(card => {
          const dxIds = state.stacCardDiagnosisIndex[String(card.id)] ?? []
          return dxIds.some(d => groupDxIds.has(d))
        })
      }

      // 2) фильтр по выбранным диагнозам (мультивыбор)
      if (state.selectedDiagnosisIds.length > 0) {
        const selected = new Set(state.selectedDiagnosisIds)
        cards = cards.filter(card => {
          const dxIds = state.stacCardDiagnosisIndex[String(card.id)] ?? []
          return dxIds.some(d => selected.has(d))
        })
      }

      return cards
    },
  },

  actions: {
    async fetchPatients() {
      if (this.isLoading) return
      this.isLoading = true

      try {
        const res = await fetch('/api/patients')
        if (!res.ok) throw new Error(`HTTP ${res.status}`)

        const data = await res.json()
        this.patients = flattenToStacCards(data)
        console.log('✅ Загружено стац-карт:', this.patients.length)
      } catch (error) {
        console.error('❌ Ошибка загрузки:', error)
      } finally {
        this.isLoading = false
      }
    },

    async fetchMeta() {
      try {
        const res = await fetch('/api/meta')
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const meta = await res.json()

        this.expertGroups = [
          { id: 'all', title: 'Все', diagnosis_ids: [] },
          ...(meta.expert_groups ?? []),
        ]
        this.diagnoses = meta.diagnoses ?? []
        this.stacCardDiagnosisIndex = meta.stac_card_diagnosis_index ?? {}

        // дефолт: первая группа (как у тебя было)
        if (!this.selectedExpertGroupId && this.expertGroups.length > 0) {
          this.selectedExpertGroupId = this.expertGroups[0].id
        }
      } catch (error) {
        console.error('❌ Ошибка загрузки meta:', error)
      }
    },

    setExpertGroup(id) {
      this.selectedExpertGroupId = id
      // сброс выбранных диагнозов при смене группы
      this.selectedDiagnosisIds = []
    },

    setSelectedDiagnosisIds(ids) {
      this.selectedDiagnosisIds = Array.isArray(ids) ? ids : []
    },
  }
})
