<script setup lang="ts">
import StatusesTable from "~/components/tables/statusesTable.vue";

definePageMeta({
  name: 'statuses',
  layout: 'admin'
})
</script>

<template>
  <statuses-table/>
</template>
