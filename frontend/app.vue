<script setup lang="ts">
import { isDemoModeEnabled } from '~/services/demoMode'

const runtimeConfig = useRuntimeConfig()
const demoMode = isDemoModeEnabled(runtimeConfig.public.demoMode)
</script>

<template>
  <NuxtLayout>
    <Message
      v-if="demoMode"
      severity="warn"
      :closable="false"
      role="status"
      class="mb-4"
    >
      Демонстрация — синтетические данные, без реального ИИ. Запросы к backend отключены.
    </Message>
      <NuxtPage />
  </NuxtLayout>
</template>
