import { computed, unref } from 'vue'

export function useDisplayedStacCards(allStacCards, currentCard, limit = 3) {
  const siblingCards = computed(() => {
    const list = unref(allStacCards) ?? []
    const current = unref(currentCard)
    if (!current?.amb_card_num) return []
    return list.filter(c => String(c.amb_card_num) === String(current.amb_card_num))
  })

  // ВАЖНО: больше не двигаем выбранную карту влево
  const displayedStacCards = computed(() => {
    const list = siblingCards.value.slice()
    return list.slice(0, limit)
  })

  const placeholdersCount = computed(() => {
    const missing = limit - displayedStacCards.value.length
    return missing > 0 ? missing : 0
  })

  return { siblingCards, displayedStacCards, placeholdersCount }
}
