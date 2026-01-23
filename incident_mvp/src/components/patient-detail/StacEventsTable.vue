<template>
  <table class="events-table">
    <thead>
      <tr>
        <th>Дата триггера</th>
        <th>Триггер</th>
        <th>Формула</th>
      </tr>
    </thead>

    <tbody>
      <tr v-for="(e, idx) in events" :key="idx" class="event-row">
        <td>{{ e.date_trigger ?? '—' }}</td>
        <td>{{ e.trigger ?? '—' }}</td>
        <td class="cell-center">—</td>
      </tr>
    </tbody>
  </table>
</template>

<script setup>
defineProps({
  events: { type: Array, required: true },
})
</script>

<style scoped>
.cell-center {
  text-align: center;
}
</style>
