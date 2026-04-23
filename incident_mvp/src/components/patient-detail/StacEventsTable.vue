<template>
  <div class="events-wrap">
    <div v-if="selectionEnabled" class="events-selection-bar">
      <span class="events-selection-bar__text">
        Выбрано событий: {{ selectedVisibleCount }}
      </span>
    </div>

    <table
      class="events-table"
      :class="{ 'events-table--selectable': selectionEnabled }"
    >
      <thead>
        <tr>
          <th v-if="selectionEnabled" class="events-table__checkbox-col">
            <input
              ref="selectAllCheckbox"
              type="checkbox"
              :checked="allVisibleSelected"
              :aria-label="
                allVisibleSelected
                  ? 'Снять выбор со всех событий'
                  : 'Выбрать все события'
              "
              @change="toggleAllVisible($event)"
            >
          </th>
          <th>Дата события</th>
          <th>Событие</th>
        </tr>
      </thead>

      <tbody>
        <tr
          v-for="event in events"
          :key="event.id"
          class="event-row"
          :class="{ 'event-row--selected': isEventSelected(event.id) }"
        >
          <td v-if="selectionEnabled" class="events-table__checkbox-col">
            <input
              type="checkbox"
              :checked="isEventSelected(event.id)"
              :aria-label="`Выбрать событие ${event.trigger ?? event.id}`"
              @change="toggleEventSelection(event.id, $event)"
            >
          </td>
          <td>{{ formatDate(event.date_trigger) }}</td>
          <td>{{ event.trigger ?? '—' }}</td>
        </tr>

        <tr v-if="events.length === 0">
          <td :colspan="columnCount" class="events-empty">Нет событий</td>
        </tr>
      </tbody>
    </table>

    <div class="event-details-panel">
      <button
        class="event-details-panel__toggle"
        type="button"
        :aria-expanded="isOpen"
        :aria-label="isOpen ? 'Скрыть детали событий' : 'Показать детали событий'"
        :title="isOpen ? 'Скрыть детали событий' : 'Показать детали событий'"
        @click="isOpen = !isOpen"
      >
        <span
          class="event-details-panel__chevron"
          :class="{ 'event-details-panel__chevron--open': isOpen }"
          aria-hidden="true"
        />
      </button>

      <div v-if="isOpen" class="event-details-panel__body">
        <template v-if="detailEvents.length > 0">
          <article
            v-for="event in detailEvents"
            :key="event.id"
            class="event-detail-card"
          >
            <header class="event-detail-card__head">
              <div class="event-detail-card__title">
                {{ event.trigger ?? 'Событие' }}
              </div>
              <div class="event-detail-card__meta">
                {{ formatDate(event.date_trigger) }}
              </div>
            </header>

            <dl class="event-detail-card__grid">
              <div
                v-for="detail in event.details"
                :key="`${event.id}:${detail.key}`"
                class="event-detail-card__row"
              >
                <dt>{{ detail.label }}</dt>
                <dd>{{ formatDetailValue(detail.value) }}</dd>
              </div>
            </dl>
          </article>
        </template>

        <div v-else class="event-details-panel__empty">
          По выбранным событиям детали пока не найдены.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

import { formatDate, formatDateTime } from '@/utils/dateFormatter'

const props = defineProps({
  events: { type: Array, required: true },
  diagnosis: { type: Object, default: null },
  selectedEventIds: { type: Array, default: () => [] },
  selectionEnabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:selectedEventIds'])

const isOpen = ref(true)
const selectAllCheckbox = ref(null)

const selectedEventIdSet = computed(
  () =>
    new Set(
      (props.selectedEventIds ?? [])
        .map((eventId) => Number(eventId))
        .filter((eventId) => Number.isFinite(eventId))
    )
)

const selectedVisibleCount = computed(() =>
  (props.events ?? []).filter((event) =>
    selectedEventIdSet.value.has(Number(event.id))
  ).length
)

const allVisibleSelected = computed(
  () =>
    props.selectionEnabled &&
    (props.events?.length ?? 0) > 0 &&
    selectedVisibleCount.value === props.events.length
)

const hasPartiallySelectedVisibleEvents = computed(
  () => selectedVisibleCount.value > 0 && !allVisibleSelected.value
)

const columnCount = computed(() => (props.selectionEnabled ? 3 : 2))

const detailEvents = computed(() => {
  const sourceEvents =
    selectedEventIdSet.value.size > 0
      ? (props.events ?? []).filter((event) =>
          selectedEventIdSet.value.has(Number(event.id))
        )
      : props.events ?? []

  return sourceEvents.filter(
    (event) => Array.isArray(event.details) && event.details.length > 0
  )
})

watch(
  [allVisibleSelected, hasPartiallySelectedVisibleEvents],
  () => {
    if (!selectAllCheckbox.value) {
      return
    }

    selectAllCheckbox.value.indeterminate =
      hasPartiallySelectedVisibleEvents.value
  },
  { immediate: true }
)

function emitSelection(nextIds) {
  emit(
    'update:selectedEventIds',
    [...new Set(nextIds.map((eventId) => Number(eventId)).filter((eventId) => Number.isFinite(eventId)))]
  )
}

function isEventSelected(eventId) {
  return selectedEventIdSet.value.has(Number(eventId))
}

function toggleEventSelection(eventId, domEvent) {
  if (!props.selectionEnabled) {
    return
  }

  const nextSelection = new Set(selectedEventIdSet.value)
  const isChecked = Boolean(domEvent?.target?.checked)

  if (isChecked) {
    nextSelection.add(Number(eventId))
  } else {
    nextSelection.delete(Number(eventId))
  }

  emitSelection([...nextSelection])
}

function toggleAllVisible(domEvent) {
  if (!props.selectionEnabled) {
    return
  }

  if (domEvent?.target?.checked) {
    emitSelection((props.events ?? []).map((event) => event.id))
    return
  }

  emitSelection([])
}

function formatDetailValue(value) {
  const raw = String(value ?? '').trim()
  if (!raw) {
    return '—'
  }

  if (/^\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2})?)?/.test(raw)) {
    return formatDateTime(raw)
  }

  return raw
}
</script>

<style scoped>
.events-wrap {
  position: relative;
}

.events-selection-bar {
  display: flex;
  align-items: center;
  padding: 14px 16px 6px;
}

.events-selection-bar__text {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}

.events-table {
  width: 100%;
  table-layout: fixed;
  border-collapse: separate;
  border-spacing: 0;
}

.events-table__checkbox-col {
  width: 34px !important;
  min-width: 34px;
  max-width: 34px;
  padding-inline: 4px !important;
  text-align: center;
}

.events-table__checkbox-col input {
  display: block;
  margin: 0 auto;
}

.events-table--selectable th:nth-child(1),
.events-table--selectable td:nth-child(1) {
  width: 34px !important;
}

.events-table--selectable th:nth-child(2),
.events-table--selectable td:nth-child(2) {
  width: 210px !important;
  text-align: left;
}

.events-table--selectable th:nth-child(3),
.events-table--selectable td:nth-child(3) {
  width: auto !important;
}

.events-table:not(.events-table--selectable) th:nth-child(1),
.events-table:not(.events-table--selectable) td:nth-child(1) {
  width: 210px !important;
  text-align: left;
}

.events-table:not(.events-table--selectable) th:nth-child(2),
.events-table:not(.events-table--selectable) td:nth-child(2) {
  width: auto !important;
}

.event-row--selected {
  background: rgba(59, 130, 246, 0.08);
}

.events-empty {
  text-align: center;
  opacity: 0.7;
}

.event-details-panel {
  border-top: 1px solid #c6ccde;
  background: linear-gradient(180deg, #ffffff 0%, #f8faff 100%);
  padding: 10px 14px 16px;
}

.event-details-panel__toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 28px;
  margin: 0 auto 2px;
  padding: 0;
  border: 1px solid rgba(148, 163, 184, 0.38);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.82);
  color: #334155;
  cursor: pointer;
  transition: background-color 0.16s ease, border-color 0.16s ease, color 0.16s ease;
}

.event-details-panel__toggle:hover {
  background: #fff;
  border-color: rgba(33, 86, 196, 0.36);
  color: #2156c4;
}

.event-details-panel__chevron {
  width: 8px;
  height: 8px;
  border-right: 2px solid currentColor;
  border-bottom: 2px solid currentColor;
  transform: translateY(-2px) rotate(45deg);
  transition: transform 0.16s ease;
}

.event-details-panel__chevron--open {
  transform: translateY(2px) rotate(225deg);
}

.event-details-panel__body {
  display: grid;
  gap: 12px;
  width: 100%;
  padding: 14px 0 0;
}

.event-detail-card {
  border: 1px solid rgba(198, 204, 222, 0.95);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 12px 26px rgba(15, 23, 42, 0.08);
  overflow: hidden;
}

.event-detail-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px 12px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.9);
  background: linear-gradient(180deg, #f7f9ff 0%, #eef4ff 100%);
}

.event-detail-card__title {
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
}

.event-detail-card__meta {
  font-size: 12px;
  color: #64748b;
  white-space: nowrap;
}

.event-detail-card__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 0;
}

.event-detail-card__row {
  padding: 12px 16px;
  border-right: 1px solid rgba(226, 232, 240, 0.9);
  border-bottom: 1px solid rgba(226, 232, 240, 0.9);
}

.event-detail-card__row dt {
  margin-bottom: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
}

.event-detail-card__row dd {
  margin: 0;
  font-size: 14px;
  line-height: 1.45;
  color: #0f172a;
  white-space: pre-wrap;
  word-break: break-word;
}

.event-details-panel__empty {
  padding: 10px 4px 4px;
  font-size: 14px;
  color: #64748b;
}

@media (max-width: 900px) {
  .events-selection-bar {
    align-items: center;
  }

  .event-detail-card__head {
    flex-direction: column;
  }

  .event-detail-card__meta {
    white-space: normal;
  }
}
</style>
