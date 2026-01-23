import { computed, unref } from 'vue'

export function useDisplayedStacCards(allStacCards, currentCard, limit = 3) {
  const siblingCards = computed(() => {
    const list = unref(allStacCards) ?? []
    const current = unref(currentCard)
    if (!current?.amb_card_num) return []
    return list.filter(c => String(c.amb_card_num) === String(current.amb_card_num))
  })

  const displayedStacCards = computed(() => {
    const current = unref(currentCard)
    const list = siblingCards.value.slice()

    if (current?.id != null) {
      const idx = list.findIndex(x => String(x.id) === String(current.id))
      if (idx > 0) {
        const [it] = list.splice(idx, 1)
        list.unshift(it)
      }
    }

    return list.slice(0, limit)
  })

  const placeholdersCount = computed(() => {
    const missing = limit - displayedStacCards.value.length
    return missing > 0 ? missing : 0
  })

  return { siblingCards, displayedStacCards, placeholdersCount }
}
