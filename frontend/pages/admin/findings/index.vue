<script setup lang="ts">
import FindingsTable from "~/components/tables/findingsTable.vue";

definePageMeta({
  name: 'findings',
  layout: 'admin'
})
</script>

<template>
  <findings-table/>
</template>
