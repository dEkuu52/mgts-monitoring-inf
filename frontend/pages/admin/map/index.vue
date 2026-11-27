<script setup lang="ts">
definePageMeta({
  name: 'map',
  layout: 'admin',
})
</script>

<template>
  <section class="card flex flex-col gap-6">
    <div>
      <p class="text-muted-color text-xs font-semibold uppercase tracking-wide m-0">Расположение</p>
      <h2 class="text-2xl font-semibold m-0">Карта</h2>
    </div>

    <div class="flex min-h-80 flex-col items-center justify-center gap-4 rounded-lg border border-dashed border-surface-300 dark:border-surface-600 p-8 text-center">
      <i class="pi pi-map text-3xl text-primary" aria-hidden="true" />
      <h3 class="text-xl font-semibold m-0">Карта пока не подключена</h3>
      <p class="text-muted-color max-w-prose m-0">
        Провайдер картографической подложки ещё не выбран. Записи с доступными координатами
        остаются в списках объектов и дефектов; здесь не отображаются вымышленные точки.
      </p>
      <Button label="Открыть список дефектов" icon="pi pi-arrow-right" icon-pos="right" as="router-link" to="/admin/findings" />
    </div>
  </section>
</template>
