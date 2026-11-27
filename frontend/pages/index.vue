<script setup lang="ts">
definePageMeta({
  layout: "default"
})


const $router = useRouter()

onMounted(async () => {
  $router.push("/admin")
})
</script>

<template>
</template>
