<template>
  <div class="events-toolbar">
    <div class="events-toolbar__left">
<!--      <div class="section-title">События</div>-->

      <div class="expert-tabs">
        <button
          v-for="g in groups"
          :key="g"
          type="button"
          class="expert-tab"
          :class="{ 'expert-tab--active': active === g }"
          @click="emit('update:active', g)"
        >
          {{ g }}
        </button>
      </div>

      <!-- новые вкладки диагнозов -->
      <div class="diagnosis-tabs">
        <button
          v-for="d in diagnoses"
          :key="d"
          type="button"
          class="diagnosis-tab"
          :class="{ 'diagnosis-tab--active': activeDiagnosis === d }"
          @click="emit('update:activeDiagnosis', d)"
        >
          {{ d }}
        </button>
      </div>
    </div>

    <div class="events-toolbar__right">
      <button class="state-btn" disabled>Принять</button>
      <button class="state-btn state-btn--red" disabled>Отклонить</button>
      <button class="state-btn" disabled>Вернуть</button>
      <button class="state-btn" disabled>Передать</button>
    </div>
  </div>
</template>


<script setup>
defineProps({
  groups: { type: Array, required: true },
  active: { type: String, required: true },
  diagnoses: { type: Array, required: true },
  activeDiagnosis: { type: String, required: true },
})

const emit = defineEmits(['update:active', 'update:activeDiagnosis'])
</script>

<style scoped>
.events-toolbar {
  display: grid;
  grid-template-columns: 1fr auto;
  grid-template-rows: auto auto;
  column-gap: 14px;
  row-gap: 6px;

  /* внутри events-panel марджины не нужны */
  margin: 0;
  padding: 10px 12px;

  border-bottom: 1px solid #c6ccde;
  background: linear-gradient(180deg, #f6f7fc 0%, #eef1fb 100%);
}

.events-toolbar__left {
  grid-column: 1;
  grid-row: 1 / span 2;
  /* твоя “табличная” укладка вкладок */
  display: grid;
  grid-template-columns: auto 1fr;
  grid-template-rows: auto auto;

  row-gap: 6px;
  align-items: center;
}

.expert-tabs { grid-column: 2; grid-row: 1; display: flex; gap: 8px; flex-wrap: wrap; }
.diagnosis-tabs { grid-column: 2; grid-row: 2; display: flex; gap: 8px; flex-wrap: wrap; }

/* КНОПКИ: строго на уровне диагнозов и ближе к таблице */
.events-toolbar__right {
  grid-column: 2;
  grid-row: 2;
  align-self: end;

  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.expert-tabs {
  grid-column: 2;
  grid-row: 1;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.expert-tab {
  border: 1px solid #c6ccde;
  background: #fff;
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 12.5px;
  cursor: pointer;
}
.expert-tab,
.diagnosis-tab {
  padding: 5px 10px;
  font-size: 12.5px;
}
.expert-tab:hover {
  background: #eaf2ff;
  border-color: #93c5fd;
}

.expert-tab--active {
  background: #2156c4;
  border-color: #2156c4;
  color: #fff;
}
.expert-tab--active,
.diagnosis-tab--active {
  box-shadow: 0 1px 0 rgba(0,0,0,0.08);
}


.diagnosis-tabs {
  grid-column: 2;
  grid-row: 2;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;

  /* “начинаются чуть правее чем вкладки экс групп” */

}

.diagnosis-tab {
  border: 1px solid #c6ccde;
  background: #fff;
  border-radius: 999px;
  padding: 5px 9px;
  font-size: 12px;
  cursor: pointer;
}

.diagnosis-tab:hover {
  background: #eaf2ff;
  border-color: #93c5fd;
}

.diagnosis-tab--active {
  background: #2156c4;
  border-color: #2156c4;
  color: #fff;
}

</style>
