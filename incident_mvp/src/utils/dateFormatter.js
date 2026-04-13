const DATE_ONLY_RE = /^\d{4}-\d{2}-\d{2}$/
const DATE_TIME_RE = /^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}/

export function formatDate(value) {
  if (!value) {
    return '—'
  }

  const raw = String(value)

  if (DATE_ONLY_RE.test(raw)) {
    const [year, month, day] = raw.split('-')
    return `${day}.${month}.${year}`
  }

  const normalized = raw.includes(' ') && !raw.includes('T') ? raw.replace(' ', 'T') : raw
  const parsed = new Date(normalized)
  if (Number.isNaN(parsed.getTime())) {
    return raw
  }

  return new Intl.DateTimeFormat('ru-RU').format(parsed)
}

export function toDateInputValue(value) {
  if (!value) {
    return ''
  }

  const raw = String(value)
  if (DATE_ONLY_RE.test(raw)) {
    return raw
  }

  const normalized = raw.includes(' ') && !raw.includes('T') ? raw.replace(' ', 'T') : raw
  const parsed = new Date(normalized)
  if (Number.isNaN(parsed.getTime())) {
    return ''
  }

  const year = parsed.getFullYear()
  const month = String(parsed.getMonth() + 1).padStart(2, '0')
  const day = String(parsed.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function formatDateTime(value) {
  if (!value) {
    return '—'
  }

  const raw = String(value)
  if (DATE_ONLY_RE.test(raw)) {
    return formatDate(raw)
  }

  const normalized = raw.includes(' ') && !raw.includes('T') ? raw.replace(' ', 'T') : raw
  const parsed = new Date(normalized)
  if (Number.isNaN(parsed.getTime())) {
    return raw
  }

  if (DATE_TIME_RE.test(raw)) {
    return new Intl.DateTimeFormat('ru-RU', {
      dateStyle: 'short',
      timeStyle: 'short',
    }).format(parsed)
  }

  return new Intl.DateTimeFormat('ru-RU').format(parsed)
}
