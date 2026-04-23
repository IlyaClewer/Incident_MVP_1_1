<template>
  <div class="events-toolbar">
    <div class="events-toolbar__top">
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

      <div v-if="modelProbability" class="model-probability">
        <div class="model-probability__label">Вероятность</div>
        <div class="model-probability__value">
          <span class="model-probability__group">{{ modelProbability.title }}</span>
          <span class="model-probability__percent">{{ modelProbability.percent }}%</span>
        </div>
      </div>
    </div>

    <div class="events-toolbar__bottom">
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

      <div class="events-toolbar__actions">
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
  modelProbability: { type: Object, default: null },
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
  grid-template-columns: minmax(0, 1fr) auto;
  grid-template-areas:
    "top model"
    "bottom actions";
  column-gap: 36px;
  row-gap: 14px;
  margin: 0;
  padding: 12px 14px 14px;
  border-bottom: 1px solid #c6ccde;
  background:
    linear-gradient(180deg, rgba(248, 250, 255, 0.98) 0%, rgba(241, 245, 252, 0.98) 100%);
}

.events-toolbar__top {
  grid-area: top;
  min-width: 0;
}

.expert-tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
  max-width: 100%;
}

.events-toolbar__bottom {
  grid-area: bottom;
  min-width: 0;
}

.diagnosis-tabs {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  padding-top: 2px;
}

.events-toolbar__actions {
  grid-area: actions;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
  align-self: end;
}

.expert-tab {
  position: relative;
  min-height: 34px;
  border: 1px solid rgba(148, 163, 184, 0.38);
  background: rgba(255, 255, 255, 0.76);
  border-radius: 10px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.25;
  color: #263a5e;
  cursor: pointer;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  transition: background-color 0.16s ease, border-color 0.16s ease, color 0.16s ease, box-shadow 0.16s ease;
}

.diagnosis-tab {
  border: 1px solid rgba(198, 204, 222, 0.95);
  background: #fff;
  border-radius: 999px;
  padding: 7px 15px;
  font-size: 13px;
  font-weight: 500;
  color: #172033;
  cursor: pointer;
  transition: background-color 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.expert-tab:not(.expert-tab--active):hover {
  background: #fff;
  border-color: rgba(33, 86, 196, 0.38);
  color: #1e4fae;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
}

.diagnosis-tab:not(.diagnosis-tab--active):hover {
  background: #eaf2ff;
  border-color: #93c5fd;
}

.expert-tab--active {
  background: #2156c4;
  border-color: #2156c4;
  color: #fff;
  box-shadow: 0 6px 14px rgba(33, 86, 196, 0.18);
}

.diagnosis-tab--active {
  background: #2156c4;
  border-color: #2156c4;
  color: #fff;
  box-shadow: 0 6px 16px rgba(33, 86, 196, 0.18);
}

.model-probability {
  grid-area: model;
  align-self: start;
  width: 420px;
  max-width: 32vw;
  padding: 8px 10px;
  border: 1px solid rgba(33, 86, 196, 0.16);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.68);
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
  backdrop-filter: blur(8px);
}

.model-probability__label {
  margin-bottom: 4px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #597097;
}

.model-probability__value {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.model-probability__group {
  font-size: 12.5px;
  font-weight: 600;
  line-height: 1.35;
  color: #1f314f;
}

.model-probability__percent {
  flex-shrink: 0;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(33, 86, 196, 0.08);
  font-size: 15px;
  font-weight: 700;
  color: #2156c4;
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
    grid-template-areas:
      "top"
      "model"
      "bottom"
      "actions";
  }

  .model-probability {
    width: 100%;
    max-width: 100%;
  }

  .events-toolbar__actions {
    justify-content: flex-start;
  }
}

@media (max-width: 720px) {
  .events-toolbar {
    padding: 10px 12px 12px;
  }

  .model-probability {
    width: 100%;
  }

  .model-probability__value {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
