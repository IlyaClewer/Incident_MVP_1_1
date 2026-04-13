function normalizeSearchValue(value) {
  return String(value ?? '')
    .toLowerCase()
    .replaceAll('ё', 'е')
    .trim()
}

function getAllowedDistance(length) {
  if (length <= 4) return 1
  if (length <= 8) return 2
  return 3
}

function levenshteinDistance(left, right) {
  const source = left ?? ''
  const target = right ?? ''

  if (source === target) return 0
  if (!source.length) return target.length
  if (!target.length) return source.length

  let previous = Array.from({ length: target.length + 1 }, (_, index) => index)

  for (let i = 0; i < source.length; i += 1) {
    const current = [i + 1]

    for (let j = 0; j < target.length; j += 1) {
      const substitutionCost = source[i] === target[j] ? 0 : 1

      current[j + 1] = Math.min(
        current[j] + 1,
        previous[j + 1] + 1,
        previous[j] + substitutionCost
      )
    }

    previous = current
  }

  return previous[target.length]
}

function matchSingleQuery(normalizedQuery, rawText) {
  const normalizedText = normalizeSearchValue(rawText)
  if (!normalizedQuery || !normalizedText) {
    return { score: 0, start: -1, end: -1, exact: false, distance: Infinity }
  }

  const exactIndex = normalizedText.indexOf(normalizedQuery)
  if (exactIndex !== -1) {
    const coverage = normalizedQuery.length / Math.max(normalizedText.length, normalizedQuery.length)

    return {
      score: 1.15 + coverage - exactIndex * 0.001,
      start: exactIndex,
      end: exactIndex + normalizedQuery.length,
      exact: true,
      distance: 0,
    }
  }

  const allowedDistance = getAllowedDistance(normalizedQuery.length)
  const candidateLengths = new Set()
  for (let delta = -allowedDistance; delta <= allowedDistance; delta += 1) {
    const candidateLength = normalizedQuery.length + delta
    if (candidateLength > 0) {
      candidateLengths.add(candidateLength)
    }
  }

  if (!candidateLengths.size) {
    candidateLengths.add(normalizedText.length)
  }

  if (normalizedText.length < Math.min(...candidateLengths)) {
    candidateLengths.add(normalizedText.length)
  }

  let bestMatch = { score: 0, start: -1, end: -1, exact: false, distance: Infinity }

  for (const candidateLength of candidateLengths) {
    const fragmentLength = Math.min(candidateLength, normalizedText.length)
    if (fragmentLength <= 0) {
      continue
    }

    for (let start = 0; start + fragmentLength <= normalizedText.length; start += 1) {
      const fragment = normalizedText.slice(start, start + fragmentLength)
      const distance = levenshteinDistance(normalizedQuery, fragment)

      if (distance > allowedDistance) {
        continue
      }

      const similarity = 1 - distance / Math.max(normalizedQuery.length, fragmentLength)
      const lengthPenalty =
        Math.abs(normalizedQuery.length - fragmentLength) /
        Math.max(normalizedQuery.length, fragmentLength)
      const score = similarity - lengthPenalty * 0.12 - start * 0.0005

      if (score > bestMatch.score) {
        bestMatch = {
          score,
          start,
          end: start + fragmentLength,
          exact: false,
          distance,
        }
      }
    }
  }

  return bestMatch
}

export function getBestTextMatch(query, text) {
  const sourceText = String(text ?? '')
  const normalizedQuery = normalizeSearchValue(query)
  if (!normalizedQuery || !sourceText.trim()) {
    return { score: 0, start: -1, end: -1, exact: false, distance: Infinity }
  }

  const compactQueryLength = normalizedQuery.replace(/\s+/g, '').length || normalizedQuery.length
  const variants = [normalizedQuery]
  const tokens = normalizedQuery
    .split(/\s+/)
    .map((token) => token.trim())
    .filter((token) => token.length >= 2)

  for (const token of tokens) {
    if (!variants.includes(token)) {
      variants.push(token)
    }
  }

  let bestMatch = { score: 0, start: -1, end: -1, exact: false, distance: Infinity }

  for (const variant of variants) {
    const rawMatch = matchSingleQuery(variant, sourceText)
    if (rawMatch.score <= 0) {
      continue
    }

    const variantWeight =
      variant === normalizedQuery
        ? 1.12
        : 0.62 + (variant.length / Math.max(compactQueryLength, variant.length)) * 0.32

    const weightedScore = rawMatch.score * variantWeight
    if (weightedScore > bestMatch.score) {
      bestMatch = {
        ...rawMatch,
        score: weightedScore,
      }
    }
  }

  return bestMatch
}

export function getBestRecordMatch(query, values) {
  const texts = (Array.isArray(values) ? values : [values])
    .map((value) => String(value ?? '').trim())
    .filter(Boolean)

  if (!texts.length) {
    return { score: 0, start: -1, end: -1, exact: false, distance: Infinity }
  }

  const combinedText = texts.join(' ')
  const candidates = combinedText ? [...texts, combinedText] : texts

  return candidates.reduce(
    (bestMatch, candidate) => {
      const match = getBestTextMatch(query, candidate)
      return match.score > bestMatch.score ? match : bestMatch
    },
    { score: 0, start: -1, end: -1, exact: false, distance: Infinity }
  )
}
