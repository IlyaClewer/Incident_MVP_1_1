import { computed, unref } from 'vue'

export function useDisplayedStacCards(allStacCards, currentCard, limit = 3) {
  const siblingCards = computed(() => {
    const list = unref(allStacCards) ?? []
    const current = unref(currentCard)

    if (!current?.amb_card_num) {
      return []
    }

    return list.filter(
      (card) => String(card.amb_card_num) === String(current.amb_card_num)
    )
  })

  const displayedStacCards = computed(() => {
    const list = siblingCards.value.slice()
    const current = unref(currentCard)

    if (list.length <= limit) {
      return list
    }

    const currentIndex = list.findIndex(
      (card) => String(card.id) === String(current?.id)
    )

    if (currentIndex === -1 || currentIndex < limit) {
      return list.slice(0, limit)
    }

    return [...list.slice(0, limit - 1), list[currentIndex]]
  })

  const placeholdersCount = computed(() => {
    const missing = limit - displayedStacCards.value.length
    return missing > 0 ? missing : 0
  })

  return { siblingCards, displayedStacCards, placeholdersCount }
}
