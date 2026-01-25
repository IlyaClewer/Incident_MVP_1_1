<template>
  <div class="events-toolbar">
    <div class="events-toolbar__left">
      <div class="expert-tabs">
        <button
          v-for="g in groups"
          :key="g.id"
          type="button"
          class="expert-tab"
          :class="{ 'expert-tab--active': active === g.id }"
          @click="emit('update:active', g.id)"
        >
          {{ g.title }}
        </button>
      </div>

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
  // [{ id: 'vascular', title: 'Сосудистые (тромбозы)' }, ...]
  groups: { type: Array, default: () => [] },
  active: { type: String, default: '' }, // groupId
  diagnoses: { type: Array, default: () => [] }, // ['ОПН', ... , 'Прочее']
  activeDiagnosis: { type: String, default: '' }, // title
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

  margin: 0;
  padding: 10px 12px;

  border-bottom: 1px solid #c6ccde;
  background: linear-gradient(180deg, #f6f7fc 0%, #eef1fb 100%);
}

.events-toolbar__left {
  grid-column: 1;
  grid-row: 1 / span 2;
  display: grid;
  grid-template-columns: auto 1fr;
  grid-template-rows: auto auto;
  row-gap: 6px;
  align-items: center;
}

.expert-tabs { grid-column: 2; grid-row: 1; display: flex; gap: 8px; flex-wrap: wrap; }
.diagnosis-tabs { grid-column: 2; grid-row: 2; display: flex; gap: 8px; flex-wrap: wrap; }

.events-toolbar__right {
  grid-column: 2;
  grid-row: 2;
  align-self: end;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.expert-tab,
.diagnosis-tab {
  border: 1px solid #c6ccde;
  background: #fff;
  border-radius: 999px;
  padding: 5px 10px;
  font-size: 12.5px;
  cursor: pointer;
}

.expert-tab:not(.expert-tab--active):hover,
.diagnosis-tab:not(.diagnosis-tab--active):hover {
  background: #eaf2ff;
  border-color: #93c5fd;
}

.expert-tab--active,
.diagnosis-tab--active {
  background: #2156c4;
  border-color: #2156c4;
  color: #fff;
  box-shadow: 0 1px 0 rgba(0,0,0,0.08);
}
</style>
