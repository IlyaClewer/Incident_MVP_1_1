<template>
  <header class="topbar">
    <div class="topbar__left topbar-left--patient">
      <button class="topbar__menu-btn topbar-back-btn" @click="emit('back')" title="Назад">
        ←
      </button>
      <span class="topbar__app-short">Стационарная карта</span>
    </div>

    <div class="topbar__right">
      <span v-if="cardNumber">{{ cardNumber }}</span>
      <span v-else>—</span>
    </div>
  </header>
</template>

<script setup>
defineProps({
  cardNumber: { type: String, default: '' },
})

const emit = defineEmits(['back'])
</script>

<style scoped>
.topbar-left--patient {
  gap: 12px;
}

.topbar-back-btn {
  display: inline-block;
}
</style>
