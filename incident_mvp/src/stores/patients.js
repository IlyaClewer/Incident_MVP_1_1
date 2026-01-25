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

function extractEventIdsFromFormulas(formulas) {
  const out = new Set()
  for (const f of (formulas ?? [])) {
    const nums = String(f).match(/\d+/g) ?? []
    for (const n of nums) out.add(Number(n))
  }
  return [...out]
}

function buildStacCardDiagnosisIndexFromDiagnoses(diagnoses) {
  const idx = {}
  for (const dx of (diagnoses ?? [])) {
    const dxId = dx?.id
    if (!dxId) continue
    for (const cardId of (dx?.stac_card_ids ?? [])) {
      const key = String(cardId)
      ;(idx[key] ||= []).push(dxId)
    }
  }
  return idx
}

export const usePatientsStore = defineStore('patients', {
  state: () => ({
    patients: [], // плоский список стац-карт
    isLoading: false,

    // meta:
    expertGroups: [],
    diagnoses: [],
    stacCardDiagnosisIndex: {}, // { [stac_card_id]: [diagnosis_id,...] }

    // derived meta:
    dxEventIdsIndex: {}, // { [diagnosis_id]: number[] } из formulas

    // filters list page:
    selectedExpertGroupId: null,
    selectedDiagnosisIds: [], // мультивыбор диагнозов
  }),

  getters: {
    getById: (state) => (id) =>
      state.patients.find(p => String(p.id) === String(id)),

    diagnosisById: (state) => (id) =>
      (state.diagnoses ?? []).find(d => String(d.id) === String(id)),

    // Диагнозы для dropdown на list page (по группе)
    availableDiagnosesForFilter: (state) => {
      if (!state.selectedExpertGroupId || state.selectedExpertGroupId === 'all') {
        return state.filteredDiagnosesNonEmpty
      }
      const g = (state.expertGroups ?? []).find(x => x.id === state.selectedExpertGroupId)
      const allowed = new Set(g?.diagnosis_ids ?? [])
      return (state.filteredDiagnosesNonEmpty ?? []).filter(d => allowed.has(d.id))
    },

    // Только диагнозы, у которых реально есть хоть одна стац-карта (иначе вкладки будут пустые)
    filteredDiagnosesNonEmpty: (state) => {
      return (state.diagnoses ?? []).filter(d => (d?.stac_card_ids?.length ?? 0) > 0)
    },

    // Для patient page: диагнозы этой эксперт-группы (и только “непустые”)
    diagnosesForGroup: (state) => (groupId) => {
      if (!groupId || groupId === 'all') return state.filteredDiagnosesNonEmpty ?? []
      const g = (state.expertGroups ?? []).find(x => x.id === groupId)
      const allowed = new Set(g?.diagnosis_ids ?? [])
      return (state.filteredDiagnosesNonEmpty ?? []).filter(d => allowed.has(d.id))
    },

    // Для patient page: диагнозы выбранной группы, которые закреплены за конкретной стац-картой
    diagnosesForCardInGroup: (state) => (stacCardId, groupId) => {
      const dxIds = state.stacCardDiagnosisIndex?.[String(stacCardId)] ?? []
      if (!groupId || groupId === 'all') {
        const set = new Set(dxIds)
        return (state.filteredDiagnosesNonEmpty ?? []).filter(d => set.has(d.id))
      }
      const g = (state.expertGroups ?? []).find(x => x.id === groupId)
      const allowed = new Set(g?.diagnosis_ids ?? [])
      const set = new Set(dxIds.filter(id => allowed.has(id)))
      return (state.filteredDiagnosesNonEmpty ?? []).filter(d => set.has(d.id))
    },

    filteredStacCards: (state) => {
      // базово: показываем карты, у которых есть события
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

        // 1) event ids по диагнозу (для фильтрации событий в пациенте)
        const dxEventIdsIndex = {}
        for (const dx of (this.diagnoses ?? [])) {
          if (!dx?.id) continue
          dxEventIdsIndex[dx.id] = extractEventIdsFromFormulas(dx.formulas)
        }
        this.dxEventIdsIndex = dxEventIdsIndex

        // 2) stacCardDiagnosisIndex: либо из бэка, либо строим из diagnoses[].stac_card_ids
        const backendIdx = meta.stac_card_diagnosis_index
        this.stacCardDiagnosisIndex =
          (backendIdx && Object.keys(backendIdx).length > 0)
            ? backendIdx
            : buildStacCardDiagnosisIndexFromDiagnoses(this.diagnoses)

        if (!this.selectedExpertGroupId && this.expertGroups.length > 0) {
          this.selectedExpertGroupId = this.expertGroups[0].id
        }
      } catch (error) {
        console.error('❌ Ошибка загрузки meta:', error)
      }
    },

    setExpertGroup(id) {
      this.selectedExpertGroupId = id
      this.selectedDiagnosisIds = []
    },

    setSelectedDiagnosisIds(ids) {
      this.selectedDiagnosisIds = Array.isArray(ids) ? ids : []
    },
  }
})
