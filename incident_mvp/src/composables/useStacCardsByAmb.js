import { computed, unref } from 'vue'

export function useStacCardsByAmb(stacCards) {
  const stacCardsByAmb = computed(() => {
    const list = unref(stacCards) ?? []
    const map = {}

    for (const card of list) {
      const amb = card?.amb_card_num
      if (amb == null) continue
      ;(map[amb] ||= []).push(card)
    }

    return map
  })

  const patientRows = computed(() => {
    const list = unref(stacCards) ?? []
    const seen = new Set()
    const out = []

    for (const card of list) {
      const amb = card?.amb_card_num
      if (amb == null) continue
      if (seen.has(amb)) continue
      seen.add(amb)

      out.push({
        amb_card_num: amb,
        patientName: card?.patientName ?? '—',

        // ✅ берём реальную дату
        birthDate: card?.birthDate ?? card?.patient_birthday ?? '—',

        // можно оставить заглушку или взять что-то реальное
        extra: card?.mht_numb ?? '—',
      })
    }

    return out
  })

  return { stacCardsByAmb, patientRows }
}
