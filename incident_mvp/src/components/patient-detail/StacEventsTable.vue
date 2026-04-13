<template>
  <div class="events-wrap">
    <table class="events-table">
      <thead>
        <tr>
          <th>Дата события</th>
          <th>Событие</th>
        </tr>
      </thead>

      <tbody>
        <tr
          v-for="event in events"
          :key="event.id"
          class="event-row"
        >
          <td>{{ formatDate(event.date_trigger) }}</td>
          <td>{{ event.trigger ?? '—' }}</td>
        </tr>

        <tr v-if="events.length === 0">
          <td colspan="2" class="events-empty">Нет событий</td>
        </tr>
      </tbody>
    </table>

    <div class="event-details-panel">
      <button
        class="event-details-panel__toggle"
        type="button"
        :aria-expanded="isOpen"
        @click="isOpen = !isOpen"
      >
        {{ isOpen ? 'Скрыть' : 'Подробнее' }}
      </button>

      <div v-if="isOpen" class="event-details-panel__body">
        <template v-if="detailEvents.length > 0">
          <article
            v-for="event in detailEvents"
            :key="event.id"
            class="event-detail-card"
          >
            <header class="event-detail-card__head">
              <div class="event-detail-card__title">{{ event.trigger ?? 'Событие' }}</div>
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
import { computed, ref } from 'vue'

import { formatDate, formatDateTime } from '@/utils/dateFormatter'

const props = defineProps({
  events: { type: Array, required: true },
  diagnosis: { type: Object, default: null },
})

const isOpen = ref(true)

const detailEvents = computed(() =>
  (props.events ?? []).filter((event) => Array.isArray(event.details) && event.details.length > 0)
)

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

.events-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.events-empty {
  text-align: center;
  opacity: 0.7;
}

.event-details-panel {
  border-top: 1px solid #c6ccde;
  background: linear-gradient(180deg, #ffffff 0%, #f8faff 100%);
}

.event-details-panel__toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 118px;
  margin: 14px 0 0 14px;
  padding: 7px 14px;
  border: 1px solid rgba(59, 130, 246, 0.22);
  border-radius: 999px;
  background: rgba(59, 130, 246, 0.08);
  color: #1d4ed8;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.event-details-panel__body {
  display: grid;
  gap: 12px;
  padding: 14px;
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
  .event-detail-card__head {
    flex-direction: column;
  }

  .event-detail-card__meta {
    white-space: normal;
  }
}
</style>
