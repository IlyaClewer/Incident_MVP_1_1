<template>
  <span v-if="!matchSegment">{{ displayText }}</span>
  <span v-else>
    {{ displayText.slice(0, matchSegment.start) }}
    <mark class="highlighted-text__mark">
      {{ displayText.slice(matchSegment.start, matchSegment.end) }}
    </mark>
    {{ displayText.slice(matchSegment.end) }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

import { getBestTextMatch } from '@/utils/fuzzySearch'

const props = defineProps({
  text: { type: [String, Number], default: '' },
  query: { type: String, default: '' },
  fallback: { type: String, default: '—' },
  minScore: { type: Number, default: 0.42 },
})

const displayText = computed(() => {
  const value = props.text
  if (value === null || value === undefined || value === '') {
    return props.fallback
  }

  return String(value)
})

const matchSegment = computed(() => {
  if (!props.query?.trim()) {
    return null
  }

  const match = getBestTextMatch(props.query, displayText.value)
  if (match.score < props.minScore || match.start < 0 || match.end <= match.start) {
    return null
  }

  return match
})
</script>

<style scoped>
.highlighted-text__mark {
  padding: 0 2px;
  border-radius: 4px;
  background: rgba(255, 221, 87, 0.55);
  color: inherit;
}
</style>
