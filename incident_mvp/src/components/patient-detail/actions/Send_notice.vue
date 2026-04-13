<template>
  <transition name="toast-fade">
    <div v-if="show" class="toast">
      {{ text }}
    </div>
  </transition>
</template>

<script setup>
defineProps({
  show: { type: Boolean, default: false },
  text: { type: String, default: 'Отправлено' },
})
</script>

<style scoped>
.toast {
  position: fixed;
  right: 18px;
  bottom: 18px;
  z-index: 2000;
  background: #111827;
  color: #fff;
  padding: 10px 12px;
  border-radius: 10px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.35);
  font-size: 13px;
}

.toast-fade-enter-active,
.toast-fade-leave-active { transition: opacity 0.16s ease, transform 0.16s ease; }
.toast-fade-enter-from,
.toast-fade-leave-to { opacity: 0; transform: translateY(6px); }
</style>
