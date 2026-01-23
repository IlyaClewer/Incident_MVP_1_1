// src/stores/patients.js
import { defineStore } from 'pinia'

// helper: делает из нового JSON плоский список стац-карт, как было раньше
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
    patients: [],  // ← теперь пусто, ждём API
    isLoading: false,
  }),

  getters: {
    getById: (state) => (id) =>
      state.patients.find(p => String(p.id) === String(id)),

    patientsWithEvents: (state) =>
      state.patients.filter(c => (c.events?.length ?? 0) > 0),
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
    }
  }
})
