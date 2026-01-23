<template>
  <th>
    <slot />
    <img
      class="th-filter-icon"
      :class="{ 'th-filter-icon--inner': inner }"
      :src="icon"
      alt=""
    />
  </th>
</template>

<script setup>
defineProps({
  icon: { type: String, required: true },
  inner: { type: Boolean, default: false },
})
</script>

<style scoped>
th {
  position: relative;
  padding-right: 26px;
}

.th-filter-icon {
  width: 14px;
  height: 14px;
  opacity: 0.65;
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
}

.th-filter-icon--inner {
  width: 12px;
  height: 12px;
  opacity: 0.45;
}
</style>
