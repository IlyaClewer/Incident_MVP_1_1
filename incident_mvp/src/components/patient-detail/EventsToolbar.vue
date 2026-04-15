<template>
  <div class="events-toolbar">
    <div class="events-toolbar__left">
      <div class="expert-tabs">
        <button
          v-for="group in groups"
          :key="group.id"
          type="button"
          class="expert-tab"
          :class="{ 'expert-tab--active': active === group.id }"
          @click="emit('update:active', group.id)"
        >
          {{ group.title }}
        </button>
      </div>

      <div class="diagnosis-tabs">
        <button
          v-for="diagnosis in diagnoses"
          :key="diagnosis"
          type="button"
          class="diagnosis-tab"
          :class="{ 'diagnosis-tab--active': activeDiagnosis === diagnosis }"
          @click="emit('update:activeDiagnosis', diagnosis)"
        >
          {{ diagnosis }}
        </button>
      </div>
    </div>

    <div class="events-toolbar__right">
      <template v-if="showDecisionButtons">
        <button
          class="state-btn"
          type="button"
          :disabled="!canChangeState || isSubmitting"
          @click="openAction('accept')"
        >
          Принять
        </button>
        <button
          class="state-btn state-btn--red"
          type="button"
          :disabled="!canChangeState || isSubmitting"
          @click="openAction('reject')"
        >
          Отклонить
        </button>
      </template>

      <button
        v-if="showReturnButton"
        class="state-btn"
        type="button"
        :disabled="!canReturn || isSubmitting"
        @click="openAction('return')"
      >
        Вернуть
      </button>

      <button
        class="state-btn"
        type="button"
        :disabled="isSubmitting"
        @click="onTransfer"
      >
        {{ transferButtonLabel }}
      </button>
    </div>
  </div>

  <BaseModal v-model:open="modalOpen" :title="modalTitle">
    <div class="modal-field-label">Комментарий</div>

    <textarea
      id="reject-reason-input"
      v-model="comment"
      class="events-toolbar__textarea"
      placeholder="Введите комментарий..."
    />

    <template #actions="{ close }">
      <button type="button" class="state-btn" @click="close">Отмена</button>
      <button
        type="button"
        class="state-btn"
        :disabled="isSubmitting"
        @click="onConfirm(close)"
      >
        {{ isSubmitting ? 'Сохраняю...' : 'Подтвердить' }}
      </button>
    </template>
  </BaseModal>

  <BaseModal v-model:open="transferModalOpen" title="Передать события">
    <div class="transfer-modal">
      <p class="transfer-modal__hint">
        Выбрано событий: {{ selectedEventsCount }}. Укажите диагноз, к которому
        нужно привязать выбранные события.
      </p>

      <label class="modal-field-label" for="transfer-target-select">
        Целевой диагноз
      </label>

      <select
        id="transfer-target-select"
        v-model="transferTargetDiagnosisStateId"
        class="transfer-modal__select"
      >
        <option
          v-for="diagnosis in transferTargetOptions"
          :key="diagnosis.value"
          :value="diagnosis.value"
        >
          {{ diagnosis.label }}
        </option>
      </select>
    </div>

    <template #actions="{ close }">
      <button type="button" class="state-btn" @click="close">Отмена</button>
      <button
        type="button"
        class="state-btn"
        :disabled="isSubmitting || !transferTargetDiagnosisStateId"
        @click="onConfirmTransfer(close)"
      >
        {{ isSubmitting ? 'Передаю...' : 'Передать' }}
      </button>
    </template>
  </BaseModal>

  <Send_notice :show="toastOpen" :text="toastText" />
</template>

<script setup>
import { computed, ref, watch } from 'vue'

import BaseModal from '@/components/patient-detail/actions/BaseModal.vue'
import Send_notice from '@/components/patient-detail/actions/Send_notice.vue'
import { usePatientsStore } from '@/stores/patients'

const props = defineProps({
  groups: { type: Array, default: () => [] },
  active: { type: [String, Number], default: '' },
  diagnoses: { type: Array, default: () => [] },
  activeDiagnosis: { type: String, default: '' },
  stacCardId: { type: [String, Number], default: null },
  diagnosisStateId: { type: [String, Number], default: null },
  diagnosisStatus: { type: String, default: '' },
  selectedEventIds: { type: Array, default: () => [] },
  transferTargetDiagnoses: { type: Array, default: () => [] },
})

const emit = defineEmits([
  'update:active',
  'update:activeDiagnosis',
  'transfer-complete',
])

const store = usePatientsStore()

const modalOpen = ref(false)
const transferModalOpen = ref(false)
const transferTargetDiagnosisStateId = ref('')
const action = ref('accept')
const comment = ref('')
const isSubmitting = ref(false)
const toastOpen = ref(false)
const toastText = ref('')

const canChangeState = computed(() => Boolean(props.diagnosisStateId))
const selectedEventsCount = computed(() => (props.selectedEventIds ?? []).length)
const normalizedStatus = computed(() => {
  switch (String(props.diagnosisStatus ?? '').toLowerCase()) {
    case 'confirmed':
    case 'approved':
    case 'accepted':
      return 'confirmed'
    case 'rejected':
      return 'rejected'
    default:
      return 'new'
  }
})
const isResolved = computed(() =>
  ['confirmed', 'rejected'].includes(normalizedStatus.value)
)
const showDecisionButtons = computed(() => !isResolved.value)
const showReturnButton = computed(() => isResolved.value)
const canReturn = computed(() => canChangeState.value && isResolved.value)
const transferTargetOptions = computed(() =>
  (props.transferTargetDiagnoses ?? []).map((diagnosis) => ({
    value: String(diagnosis.diagnosisStateId),
    label: `${diagnosis.title ?? diagnosis.name ?? diagnosis.id} | ${formatStatusLabel(diagnosis.status)}`,
  }))
)
const transferButtonLabel = computed(() =>
  selectedEventsCount.value > 0
    ? `Передать (${selectedEventsCount.value})`
    : 'Передать'
)

const modalTitle = computed(() => {
  switch (action.value) {
    case 'accept':
      return 'Принять'
    case 'reject':
      return 'Отклонить'
    case 'return':
      return 'Вернуть'
    default:
      return 'Действие'
  }
})

watch(
  transferTargetOptions,
  (targets) => {
    const currentValue = String(transferTargetDiagnosisStateId.value ?? '')
    const hasCurrentTarget = targets.some(
      (target) => String(target.value) === currentValue
    )

    if (!hasCurrentTarget) {
      transferTargetDiagnosisStateId.value = targets[0]?.value ?? ''
    }
  },
  { immediate: true }
)

function formatStatusLabel(status) {
  switch (String(status ?? '').toLowerCase()) {
    case 'confirmed':
    case 'approved':
    case 'accepted':
      return 'подтвержден'
    case 'rejected':
      return 'отклонен'
    default:
      return 'новый'
  }
}

function showToast(text) {
  toastText.value = text
  toastOpen.value = true
  window.setTimeout(() => {
    toastOpen.value = false
  }, 1800)
}

function openAction(type) {
  if (!canChangeState.value) {
    return
  }

  if (type === 'return' && !canReturn.value) {
    return
  }

  action.value = type
  comment.value = ''
  modalOpen.value = true
}

function onTransfer() {
  if (!props.diagnosisStateId) {
    showToast('Сначала выберите диагноз')
    return
  }

  if (selectedEventsCount.value === 0) {
    showToast('Сначала отметьте события для передачи')
    return
  }

  if (transferTargetOptions.value.length === 0) {
    showToast('Для этой группы пока нет другого диагноза')
    return
  }

  transferTargetDiagnosisStateId.value = transferTargetOptions.value[0]?.value ?? ''
  transferModalOpen.value = true
}

async function onConfirm(close) {
  if (!props.diagnosisStateId) {
    close()
    return
  }

  const targetStatusByAction = {
    accept: 'confirmed',
    reject: 'rejected',
    return: 'new',
  }

  const targetStatus = targetStatusByAction[action.value]
  if (!targetStatus) {
    close()
    return
  }

  isSubmitting.value = true

  try {
    await store.updateDiagnosisState(props.diagnosisStateId, {
      status: targetStatus,
      comment: comment.value?.trim() || undefined,
    })

    showToast('Статус сохранен')
    close()
  } catch (error) {
    showToast(
      error instanceof Error ? error.message : 'Не удалось сохранить статус'
    )
  } finally {
    isSubmitting.value = false
  }
}

async function onConfirmTransfer(close) {
  if (!props.diagnosisStateId || !transferTargetDiagnosisStateId.value) {
    return
  }

  const eventIds = (props.selectedEventIds ?? [])
    .map((eventId) => Number(eventId))
    .filter((eventId) => Number.isFinite(eventId))

  if (eventIds.length === 0) {
    showToast('Сначала отметьте события для передачи')
    return
  }

  isSubmitting.value = true

  try {
    await store.transferDiagnosisEvents(
      props.diagnosisStateId,
      {
        event_ids: eventIds,
        target_diagnosis_state_id: Number(transferTargetDiagnosisStateId.value),
      },
      { stacCardId: props.stacCardId }
    )

    emit('transfer-complete')
    showToast(eventIds.length === 1 ? 'Событие передано' : 'События переданы')
    close()
  } catch (error) {
    showToast(
      error instanceof Error ? error.message : 'Не удалось передать события'
    )
  } finally {
    isSubmitting.value = false
  }
}
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

.expert-tabs {
  grid-column: 2;
  grid-row: 1;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.diagnosis-tabs {
  grid-column: 2;
  grid-row: 2;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

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
  box-shadow: 0 1px 0 rgba(0, 0, 0, 0.08);
}

.modal-field-label {
  margin-top: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}

.events-toolbar__textarea,
.transfer-modal__select {
  width: 100%;
  margin-top: 8px;
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  font: inherit;
  color: #0f172a;
  background: #fff;
}

.events-toolbar__textarea {
  min-height: 120px;
  resize: vertical;
}

.transfer-modal {
  display: grid;
  gap: 10px;
}

.transfer-modal__hint {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: #475569;
}

@media (max-width: 980px) {
  .events-toolbar {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto;
  }

  .events-toolbar__left {
    grid-column: 1;
    grid-row: 1;
  }

  .events-toolbar__right {
    grid-column: 1;
    grid-row: 2;
    justify-content: flex-start;
  }
}

@media (max-width: 720px) {
  .events-toolbar__left {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto;
  }

  .expert-tabs,
  .diagnosis-tabs {
    grid-column: 1;
  }
}
</style>
