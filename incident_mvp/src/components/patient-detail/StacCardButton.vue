<template>
  <button
    class="info-card info-card--stac stac-card-btn"
    :class="{ 'info-card--active': active }"
    type="button"
    :title="card.cardNumber"
    @click="emit('select', card.id)"
  >
    <div class="info-card__title">Стац. карта</div>

    <div class="info-row">
      <div class="info-key">№</div>
      <div class="info-val info-val--mono">{{ card.cardNumber ?? '—' }}</div>
    </div>

    <div class="info-row">
      <div class="info-key">Госпит.</div>
      <div class="info-val">{{ formatDate(card.date_hosp) }}</div>
    </div>

    <div class="info-row">
      <div class="info-key">Операция</div>
      <div class="info-val">{{ formatDate(card.date_operation ?? card.date_hosp) }}</div>
    </div>

    <div class="info-row info-row--last">
      <div class="info-key">Выписка</div>
      <div class="info-val">{{ formatDate(card.date_discharge) }}</div>
    </div>

    <div class="info-row info-row--last">
      <div class="info-key">Статус</div>
      <div class="info-val">{{ card.status ?? 'new' }}</div>
    </div>
  </button>
</template>

<script setup>
import { formatDate } from '@/utils/dateFormatter'

defineProps({
  card: { type: Object, required: true },
  active: { type: Boolean, default: false },
})

const emit = defineEmits(['select'])
</script>

<style scoped>
.info-card {
  border: 1px solid #c6ccde;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 10px 22px rgba(15, 23, 42, 0.08);
  padding: 12px 14px;
}

.info-card--stac {
  flex: 0 0 auto;
  width: 210px;
  box-sizing: border-box;
}

.info-card__title {
  font-weight: 700;
  margin-bottom: 10px;
  opacity: 0.9;
}

.info-row {
  display: grid;
  grid-template-columns: 72px 1fr;
  gap: 10px;
  padding: 6px 0;
  border-bottom: 1px solid #eef0f7;
}

.info-row--last {
  border-bottom: none;
}

.info-key {
  font-size: 12.5px;
  opacity: 0.75;
}

.info-val {
  font-size: 13px;
}

.info-val--mono {
  font-variant-numeric: tabular-nums;
}

.stac-card-btn {
  cursor: pointer;
  text-align: left;
  box-sizing: border-box;
  border: 1px solid rgba(198, 204, 222, 0.85);
  background: #fff;
  box-shadow:
    0 0 0 2px rgba(33, 86, 196, 0),
    0 10px 22px rgba(15, 23, 42, 0.08);
}

.stac-card-btn:hover {
  border-color: #93c5fd;
  box-shadow: 0 0 0 2px rgba(147, 197, 253, 0.6), 0 10px 22px rgba(15, 23, 42, 0.08);
}

.info-card--active {
  border-color: #2156c4;
  box-shadow:
    0 0 0 2px rgba(33, 86, 196, 0.25),
    0 10px 22px rgba(15, 23, 42, 0.08);
}
</style>
