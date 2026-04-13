<template>
  <Teleport to="body">
    <div
      class="modal-backdrop"
      :class="{ 'is-open': open }"
      @click.self="close"
    >
      <div class="modal-dialog" role="dialog" aria-modal="true" @click.stop>
        <h3 v-if="title">{{ title }}</h3>

        <div class="modal-body">
          <slot />
        </div>

        <div class="modal-actions">
          <slot name="actions" :close="close" :confirm="confirm" />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { onBeforeUnmount, onMounted } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '' },
  closeOnEsc: { type: Boolean, default: true },
})

const emit = defineEmits(['update:open', 'confirm'])

function close() {
  emit('update:open', false)
}

function confirm() {
  emit('confirm')          // просто событие (для UI уведомления)
  emit('update:open', false)
}

function onKeydown(e) {
  if (!props.open) return
  if (props.closeOnEsc && e.key === 'Escape') close()
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>
