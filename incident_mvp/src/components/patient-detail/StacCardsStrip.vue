<template>
  <div class="stac-cards">
    <StacCardButton
      v-for="c in cards"
      :key="c.id"
      :card="c"
      :active="String(c.id) === String(activeId)"
      @select="emit('select', $event)"
    />

    <div
      v-for="n in placeholdersCount"
      :key="'ph-' + n"
      class="info-card info-card--stac info-card--placeholder"
    >
      <div class="info-card__title">Стац. карта</div>
      <div class="placeholder-text">Нет данных</div>
    </div>
  </div>
</template>

<script setup>
import StacCardButton from './StacCardButton.vue'

defineProps({
  cards: { type: Array, required: true },
  activeId: { type: [String, Number], required: true },
  placeholdersCount: { type: Number, default: 0 },
})

const emit = defineEmits(['select'])
</script>

<style scoped>
.stac-cards {
  display: flex;
  gap: 25px;
  align-items: flex-start;
  flex-wrap: nowrap;
  overflow-x: auto;
  padding-bottom: 2px;
}

/* ВАЖНО: плейсхолдеры используют классы info-card--stac,
   но стили из StacCardButton.vue сюда не попадут из-за scoped,
   поэтому задаём размер тут же */
.info-card--stac {
  flex: 0 0 auto;
  width: 210px;          /* должно совпадать с StacCardButton.vue */
  box-sizing: border-box;
}

/* Плейсхолдеры: те же габариты/отступы/рамка, что и обычная стац-карта */
.info-card--placeholder {
  border: 1px solid rgba(198, 204, 222, 0.85);
  background: #fff;
  border-radius: 12px;
  padding: 12px 14px;
  flex: 0 0 auto;
  width: 210px;          /* тоже 210px */
  min-height: 190px;     /* чтобы по высоте не “сплющивались” */
  box-sizing: border-box;
  opacity: 0.65;
  box-shadow: 0 10px 22px rgba(15, 23, 42, 0.08);
}

.placeholder-text {
  opacity: 0.75;
  font-size: 13px;
  padding: 6px 0;
}

@media (max-width: 1200px) {
  .stac-cards {
    flex-wrap: wrap;
    overflow-x: visible;
    gap: 12px;
  }

  .info-card--stac,
  .info-card--placeholder {
    width: min(100%, 720px);
  }
}
</style>


