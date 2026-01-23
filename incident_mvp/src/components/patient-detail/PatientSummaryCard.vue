<template>
  <div class="info-card info-card--patient">
    <div class="info-card__title">Пациент</div>

    <div class="info-row">
      <div class="info-key">ФИО</div>
      <div class="info-val">{{ card.patientName ?? '—' }}</div>
    </div>

    <div class="info-row">
      <div class="info-key">Дата рождения</div>
      <div class="info-val">{{ card.birthDate ?? '—' }}</div>
    </div>

    <div class="info-row info-row--last">
      <div class="info-key">Отделение</div>
      <div class="info-val">{{ card.department ?? '—' }}</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  card: { type: Object, required: true },
})

</script>

<style scoped>
.info-card {
  border: 1px solid #c6ccde;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 10px 22px rgba(15, 23, 42, 0.08);
  padding: 12px 14px;
}

.info-card--patient {
  flex: 0 0 auto;
  width: 460px;
}

.info-card__title {
  font-weight: 700;
  margin-bottom: 10px;
  opacity: 0.9;
}

.info-row {
  display: grid;
  grid-template-columns: 92px 1fr;
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
</style>
