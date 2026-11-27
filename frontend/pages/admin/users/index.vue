<script setup lang="ts">
import UsersTable from "~/components/tables/usersTable.vue";

definePageMeta({
  name: 'users',
  layout: 'admin'
})
</script>

<template>
  <users-table/>
</template>
