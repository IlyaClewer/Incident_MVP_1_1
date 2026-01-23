<template>
  <table class="stac-table">
    <thead>
      <tr>
        <TableHeaderCell :icon="filterIconUrl" inner>№ стац. карты</TableHeaderCell>
        <TableHeaderCell :icon="filterIconUrl" inner>Отделение</TableHeaderCell>
        <TableHeaderCell :icon="filterIconUrl" inner>Дата госпит.</TableHeaderCell>
        <TableHeaderCell :icon="filterIconUrl" inner>Дата операции</TableHeaderCell>
        <TableHeaderCell :icon="filterIconUrl" inner>Дата выписки</TableHeaderCell>
        <TableHeaderCell :icon="filterIconUrl" inner>Статус</TableHeaderCell>
      </tr>
    </thead>

    <tbody>
      <tr
        v-for="card in cards"
        :key="card.id"
        class="stac-row"
        @click.stop="emit('open-stac-card', card.id)"
      >
        <td class="stac-link">{{ card.cardNumber ?? '—' }}</td>
        <td class="cell-center">{{ card.department ?? '—' }}</td>
        <td class="cell-center">{{ card.date_hosp ?? '—' }}</td>
        <td class="cell-center">{{ card.date_operation ?? card.date_hosp ?? '—' }}</td>
        <td class="cell-center">{{ card.date_discharge ?? '—' }}</td>
        <td class="status-cell status-cell--center" :data-status="card.status ?? 'new'">
          <span class="status-pill">{{ card.status ?? 'new' }}</span>
        </td>
      </tr>

      <tr v-if="cards.length === 0">
        <td colspan="6" class="stac-empty">Нет стац. карт</td>
      </tr>
    </tbody>
  </table>
</template>

<script setup>
import TableHeaderCell from './TableHeaderCell.vue'
import filterIconUrl from '@/assets/img/filter.svg'

const props = defineProps({
  cards: { type: Array, required: true },
})

const emit = defineEmits(['open-stac-card'])
</script>

<style scoped>
/* важно: глобальный .events-table задаёт fixed + sticky, тут делаем “обычную” таблицу */
.stac-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: auto;
  background: #fff;
  border: 1px solid rgba(77, 79, 86, 0.55);
  box-shadow: 0 0 0 1px rgba(17, 24, 39, 0.14);
  border-radius: 10px;
  overflow: hidden;
}

/* сетка как у основной таблицы */
.stac-table th,
.stac-table td {
  width: auto;
  padding: 6px 8px;
  border-bottom: 1px solid rgba(17, 24, 39, 0.12);
  border-right: 1px solid rgba(17, 24, 39, 0.12);
  background: #fff;
  font-size: 12px;
  vertical-align: middle;
  white-space: nowrap;
}

.stac-table th:last-child,
.stac-table td:last-child {
  border-right: none;
}

.stac-table tbody tr:last-child td {
  border-bottom: none;
}

.stac-table thead th {
  background: linear-gradient(180deg, #f8f9fe 0%, #eaecf6 100%);
  font-weight: 700;
}

.stac-row {
  cursor: pointer;
}

.stac-row:hover td {
  background: #eef4ff;
}

.stac-link {
  color: #2156c4;
  text-decoration: underline;
  white-space: nowrap;
}

.cell-center {
  text-align: center;
}

.status-cell--center {
  text-align: center;
}

.status-cell--center .status-pill {
  margin: 0 auto;
}

.stac-empty {
  padding: 10px;
  opacity: 0.7;
  text-align: center;
}
</style>
