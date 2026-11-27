<script setup lang="ts">
import { useRequest } from '~/services/useRequest'

const loading = ref(true)
const loadError = ref('')
const statuses = ref<Record<string, any>[]>([])

const request = await useRequest('/api/statuses')
loading.value = false

if (request.error) {
  loadError.value = request.error.description || 'Не удалось загрузить список статусов.'
} else if (Array.isArray(request.data)) {
  statuses.value = request.data
}
</script>

<template>
  <section class="card">
    <Toolbar class="mb-6">
      <template #start>
        <Button label="Добавить статус" icon="pi pi-plus" as="router-link" to="/admin/statuses/action" />
      </template>
    </Toolbar>

    <Message v-if="loadError" severity="error" :closable="false" class="mb-4">{{ loadError }}</Message>
    <DataTable
      :value="statuses"
      data-key="id"
      :loading="loading"
      :paginator="statuses.length > 8"
      :rows="8"
      :rows-per-page-options="[8, 16, 32]"
      striped-rows
      scrollable
      table-style="min-width: 36rem"
    >
      <template #header>
        <div class="flex flex-wrap gap-2 items-center justify-between">
          <div>
            <p class="text-muted-color text-xs font-semibold uppercase tracking-wide m-0">Справочник</p>
            <h2 class="m-0 text-xl font-semibold">Статусы</h2>
          </div>
        </div>
      </template>
      <Column field="id" header="ID" sortable />
      <Column field="type" header="Тип" sortable>
        <template #body="{ data }">{{ data.type || '—' }}</template>
      </Column>
      <Column field="description" header="Описание">
        <template #body="{ data }">{{ data.description || '—' }}</template>
      </Column>
      <Column header="Действие" header-style="width: 5rem">
        <template #body="{ data }">
          <Button
            as="router-link"
            :to="{ path: '/admin/statuses/action', query: { id: data.id } }"
            icon="pi pi-pencil"
            text
            rounded
            severity="secondary"
            :aria-label="`Редактировать статус ${data.type || data.id}`"
          />
        </template>
      </Column>
      <template #empty>
        <div class="flex flex-col items-center justify-center gap-2 py-8 text-muted-color">
          <i class="pi pi-inbox text-2xl" aria-hidden="true" />
          <span>{{ loadError ? 'Список временно недоступен' : 'Статусы не найдены' }}</span>
        </div>
      </template>
    </DataTable>
  </section>
</template>
