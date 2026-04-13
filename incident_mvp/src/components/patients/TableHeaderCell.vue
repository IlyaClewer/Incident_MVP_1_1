<template>
  <th v-click-outside="close" class="table-header-cell">
    <div class="table-header-cell__inner">
      <span class="table-header-cell__label">
        <slot />
      </span>

      <button
        v-if="hasFilter"
        class="table-header-cell__btn"
        :class="{
          'table-header-cell__btn--active': active,
          'table-header-cell__btn--inner': inner,
        }"
        type="button"
        @click.stop="toggle"
      >
        <img
          class="table-header-cell__icon"
          :src="icon"
          alt=""
        />
      </button>
    </div>

    <div
      v-if="hasFilter && isOpen"
      class="table-header-cell__popover"
      @click.stop
    >
      <slot name="filter" :close="close" />
    </div>
  </th>
</template>

<script setup>
import { computed, ref, useSlots } from 'vue'

const props = defineProps({
  icon: { type: String, required: true },
  inner: { type: Boolean, default: false },
  active: { type: Boolean, default: false },
})

const slots = useSlots()
const isOpen = ref(false)

const hasFilter = computed(() => Boolean(slots.filter))

const vClickOutside = {
  mounted(el, binding) {
    el.__clickOutsideHandler__ = (event) => {
      if (!el.contains(event.target)) {
        binding.value(event)
      }
    }

    document.addEventListener('click', el.__clickOutsideHandler__)
  },
  unmounted(el) {
    document.removeEventListener('click', el.__clickOutsideHandler__)
  },
}

function toggle() {
  isOpen.value = !isOpen.value
}

function close() {
  isOpen.value = false
}
</script>

<style scoped>
.table-header-cell {
  position: relative;
  padding-right: 10px;
}

.table-header-cell__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.table-header-cell__label {
  min-width: 0;
}

.table-header-cell__btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border: 1px solid transparent;
  border-radius: 999px;
  background: transparent;
  cursor: pointer;
  transition:
    background-color 160ms ease,
    border-color 160ms ease,
    transform 160ms ease;
}

.table-header-cell__btn:hover {
  background: rgba(59, 130, 246, 0.10);
  border-color: rgba(59, 130, 246, 0.18);
}

.table-header-cell__btn--active {
  background: rgba(59, 130, 246, 0.14);
  border-color: rgba(59, 130, 246, 0.28);
}

.table-header-cell__btn--inner {
  width: 20px;
  height: 20px;
}

.table-header-cell__icon {
  width: 14px;
  height: 14px;
  opacity: 0.7;
}

.table-header-cell__btn--active .table-header-cell__icon {
  opacity: 1;
}

.table-header-cell__popover {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  z-index: 50;
  min-width: 220px;
  max-width: 280px;
  padding: 12px;
  background: #fff;
  border: 1px solid rgba(198, 204, 222, 0.95);
  border-radius: 12px;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.18);
}
</style>
