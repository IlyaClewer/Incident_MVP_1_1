<template>
  <div class="dx-dropdown" v-click-outside="close">
    <button class="dx-btn" type="button" @click="toggle">
      Диагнозы
      <span v-if="selectedCount > 0" class="dx-badge">{{ selectedCount }}</span>
    </button>

    <div v-if="isOpen" class="dx-panel">
      <div v-if="diagnoses.length === 0" class="dx-empty">
        Нет диагнозов
      </div>

      <label v-for="d in diagnoses" :key="d.id" class="dx-item">
        <input type="checkbox" :value="d.id" v-model="selectedIds" />
        <span class="dx-name">{{ d.name }}</span>
      </label>

      <button class="dx-reset" type="button" @click="reset">Сброс</button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  diagnoses: { type: Array, default: () => [] },
  modelValue: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:modelValue'])

const isOpen = ref(false)

const selectedIds = computed({
  get: () => (Array.isArray(props.modelValue) ? props.modelValue : []),
  set: (val) => emit('update:modelValue', Array.isArray(val) ? val : []),
})

const selectedCount = computed(() => selectedIds.value.length)

const vClickOutside = {
  mounted(el, binding) {
    el.__clickOutsideHandler__ = (event) => {
      if (!el.contains(event.target)) binding.value(event)
    }

    el.__escapeHandler__ = (event) => {
      if (event.key === 'Escape') {
        binding.value(event)
      }
    }

    document.addEventListener('pointerdown', el.__clickOutsideHandler__, true)
    document.addEventListener('keydown', el.__escapeHandler__)
  },
  unmounted(el) {
    document.removeEventListener('pointerdown', el.__clickOutsideHandler__, true)
    document.removeEventListener('keydown', el.__escapeHandler__)
  },
}

// Если поменялась группа и список диагнозов стал другим — подчистим выбранные,
// но эмитим только если реально что-то удалили (без бесконечного цикла)
watch(
  () => props.diagnoses,
  (dx) => {
    const allowed = new Set((dx ?? []).map(d => d.id))
    const cleaned = selectedIds.value.filter(id => allowed.has(id))
    if (cleaned.length !== selectedIds.value.length) {
      emit('update:modelValue', cleaned)
    }
  },
  { deep: true }
)

function toggle() {
  isOpen.value = !isOpen.value
}

function close() {
  isOpen.value = false
}

function reset() {
  emit('update:modelValue', [])
}
</script>


<style scoped>
.dx-dropdown {
  position: relative;
  display: inline-block;
  z-index: 1300;
}

.dx-btn {
  padding: 6px 10px;
  border: 1px solid #c6ccde;
  border-radius: 8px;
  font-size: 13px;
  background: #fff;
  cursor: pointer;
}

.dx-badge {
  margin-left: 8px;
  padding: 1px 6px;
  border-radius: 999px;
  background: #2156c4;
  color: #fff;
  font-size: 12px;
}

.dx-panel {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  width: 360px;
  max-height: 280px;
  overflow: auto;

  background: #fff;
  border: 1px solid rgba(198, 204, 222, 0.95);
  border-radius: 12px;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.18);
  padding: 10px;
  z-index: 1300;
}

.dx-item {
  display: flex;
  gap: 10px;
  padding: 6px 6px;
  border-radius: 8px;
  font-size: 13px;
}

.dx-item:hover {
  background: #eef4ff;
}

.dx-name {
  line-height: 1.2;
}

.dx-empty {
  opacity: 0.7;
  padding: 8px 6px;
  font-size: 13px;
}

.dx-reset {
  width: 100%;
  margin-top: 10px;
  padding: 8px 10px;
  border: 1px solid rgba(198, 204, 222, 0.95);
  border-radius: 10px;
  background: #f3f4f6;
  cursor: pointer;
  font-size: 13px;
}
</style>
