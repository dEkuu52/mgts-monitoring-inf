<template>
  <svg class="spr-icon" :class="`spr-${name}`">
    <use class="spr-icon__use" :href="`#${name}`"></use>
  </svg>
</template>

<script setup lang="ts">
defineProps<{
  name: string
}>()
</script>
