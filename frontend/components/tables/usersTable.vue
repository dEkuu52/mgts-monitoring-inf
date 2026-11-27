<script setup lang="ts">
import { useFilters } from '~/composables/useFilters'
import { useRequest } from '~/services/useRequest'

const { dateFormat } = useFilters()
const loading = ref(true)
const loadError = ref('')
const users = ref<Record<string, any>[]>([])

const request = await useRequest('/api/users')
loading.value = false

if (request.error) {
  loadError.value = request.error.description || 'Не удалось загрузить список пользователей.'
} else if (Array.isArray(request.data)) {
  users.value = request.data
}
</script>

<template>
  <section class="card">
    <Toolbar class="mb-6">
      <template #start>
        <Button label="Добавить пользователя" icon="pi pi-plus" as="router-link" to="/admin/users/action" />
      </template>
    </Toolbar>

    <Message v-if="loadError" severity="error" :closable="false" class="mb-4">{{ loadError }}</Message>
    <DataTable
      :value="users"
      data-key="id"
      :loading="loading"
      :paginator="users.length > 8"
      :rows="8"
      :rows-per-page-options="[8, 16, 32]"
      striped-rows
      scrollable
      table-style="min-width: 68rem"
    >
      <template #header>
        <div class="flex flex-wrap gap-2 items-center justify-between">
          <div>
            <p class="text-muted-color text-xs font-semibold uppercase tracking-wide m-0">Учётные записи</p>
            <h2 class="m-0 text-xl font-semibold">Пользователи</h2>
          </div>
        </div>
      </template>
      <Column field="id" header="ID" sortable />
      <Column field="username" header="Имя пользователя" sortable>
        <template #body="{ data }">{{ data.username || '—' }}</template>
      </Column>
      <Column field="email" header="E-mail" sortable>
        <template #body="{ data }">{{ data.email || '—' }}</template>
      </Column>
      <Column field="phone" header="Номер телефона">
        <template #body="{ data }">{{ data.phone || '—' }}</template>
      </Column>
      <Column field="role" header="Роль" sortable>
        <template #body="{ data }">{{ data.role || '—' }}</template>
      </Column>
      <Column field="created_at" header="Создан" sortable>
        <template #body="{ data }">{{ data.created_at ? dateFormat(data.created_at) : '—' }}</template>
      </Column>
      <Column field="updated_at" header="Обновлён" sortable>
        <template #body="{ data }">{{ data.updated_at ? dateFormat(data.updated_at) : '—' }}</template>
      </Column>
      <Column header="Действие" header-style="width: 5rem">
        <template #body="{ data }">
          <Button
            as="router-link"
            :to="{ path: '/admin/users/action', query: { id: data.id } }"
            icon="pi pi-pencil"
            text
            rounded
            severity="secondary"
            :aria-label="`Редактировать пользователя ${data.username || data.id}`"
          />
        </template>
      </Column>
      <template #empty>
        <div class="flex flex-col items-center justify-center gap-2 py-8 text-muted-color">
          <i class="pi pi-inbox text-2xl" aria-hidden="true" />
          <span>{{ loadError ? 'Список временно недоступен' : 'Пользователи не найдены' }}</span>
        </div>
      </template>
    </DataTable>
  </section>
</template>
