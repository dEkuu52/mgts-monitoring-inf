<script setup lang="ts">
import { useRequest } from '~/services/useRequest'

const STATUS_LABELS: Record<string, string> = {
  ok: 'В норме',
  check_required: 'Требуется проверка',
  repair_required: 'Требуется ремонт',
  unrecognized: 'Не распознано',
}

const PROCESSING_LABELS: Record<string, string> = {
  awaiting_processing: 'Ожидает обработки',
  awating_processing: 'Ожидает обработки',
  pending: 'Ожидает обработки',
  processing: 'Обрабатывается',
  done: 'Обработано',
  failed: 'Ошибка',
}

const loading = ref(true)
const loadError = ref('')
const statusError = ref('')
const objects = ref<Record<string, any>[]>([])
const statuses = ref<Record<string, any>[]>([])

const [objectsResponse, statusesResponse] = await Promise.all([
  useRequest('/api/infrastructure-objects'),
  useRequest('/api/statuses'),
])
loading.value = false

if (objectsResponse.error) {
  loadError.value = objectsResponse.error.description || 'Не удалось загрузить список объектов.'
} else if (Array.isArray(objectsResponse.data)) {
  objects.value = objectsResponse.data
}

if (statusesResponse.error) {
  statusError.value = 'Не удалось загрузить справочник статусов; показаны идентификаторы.'
} else if (Array.isArray(statusesResponse.data)) {
  statuses.value = statusesResponse.data
}

const statusesById = computed(() => Object.fromEntries(
  statuses.value.map(status => [String(status.id), status]),
))
const hasProcessing = computed(() => objects.value.some(item => !!item.processing_status))

function statusLabel(item: Record<string, any>) {
  const status = statusesById.value[String(item.status_id)]
  return STATUS_LABELS[status?.type] || status?.type || item.status_id || '—'
}

function statusDescription(item: Record<string, any>) {
  return statusesById.value[String(item.status_id)]?.description || ''
}

function processingLabel(item: Record<string, any>) {
  const state = item.processing_status
  return state ? (PROCESSING_LABELS[state] || state) : '—'
}

function processingSeverity(item: Record<string, any>) {
  if (item.processing_status === 'failed') return 'danger'
  if (item.processing_status === 'processing') return 'info'
  if (item.processing_status === 'done') return 'success'
  return 'warn'
}

function statusSeverity(item: Record<string, any>) {
  const status = statusesById.value[String(item.status_id)]?.type
  if (status === 'repair_required') return 'danger'
  if (status === 'check_required') return 'warn'
  if (status === 'ok') return 'success'
  return 'secondary'
}
</script>

<template>
  <section class="card">
    <Toolbar class="mb-6">
      <template #start>
        <Button label="Добавить объект" icon="pi pi-plus" as="router-link" to="/admin/objects/action" />
      </template>
    </Toolbar>

    <Message v-if="loadError" severity="error" :closable="false" class="mb-4">{{ loadError }}</Message>
    <Message v-else-if="statusError" severity="warn" :closable="false" class="mb-4">{{ statusError }}</Message>

    <DataTable
      :value="objects"
      data-key="id"
      :loading="loading"
      :paginator="objects.length > 8"
      :rows="8"
      :rows-per-page-options="[8, 16, 32]"
      striped-rows
      scrollable
      table-style="min-width: 76rem"
    >
      <template #header>
        <div class="flex flex-wrap gap-2 items-center justify-between">
          <div>
            <p class="text-muted-color text-xs font-semibold uppercase tracking-wide m-0">Реестр инфраструктуры</p>
            <h2 class="m-0 text-xl font-semibold">Объекты</h2>
          </div>
        </div>
      </template>
      <Column field="id" header="ID" sortable />
      <Column header="Фото" header-style="width: 6rem">
        <template #body="{ data }">
          <Image
            v-if="data.img_url"
            :src="data.img_url"
            alt="Фото объекта"
            image-class="h-12 w-16 rounded-md border border-surface-200 dark:border-surface-700 object-cover"
            preview
          />
          <span v-else class="text-sm text-muted-color">Нет фото</span>
        </template>
      </Column>
      <Column field="type" header="Тип" sortable>
        <template #body="{ data }">{{ data.type || '—' }}</template>
      </Column>
      <Column field="external_id" header="Внешний идентификатор" sortable>
        <template #body="{ data }">{{ data.external_id || '—' }}</template>
      </Column>
      <Column field="place" header="Место">
        <template #body="{ data }">{{ data.place || '—' }}</template>
      </Column>
      <Column header="Координаты">
        <template #body="{ data }">
          {{ data.lat != null && data.lon != null ? `${data.lat}, ${data.lon}` : '—' }}
        </template>
      </Column>
      <Column field="status_id" header="Статус" sortable>
        <template #body="{ data }">
          <Tag :value="statusLabel(data)" :severity="statusSeverity(data)" :title="statusDescription(data)" />
        </template>
      </Column>
      <Column v-if="hasProcessing" header="Обработка">
        <template #body="{ data }">
          <Tag :value="processingLabel(data)" :severity="processingSeverity(data)" :title="data.processing_error || ''" />
        </template>
      </Column>
      <Column header="Действие" header-style="width: 5rem">
        <template #body="{ data }">
          <Button
            as="router-link"
            :to="{ path: '/admin/objects/action', query: { id: data.id } }"
            icon="pi pi-pencil"
            text
            rounded
            severity="secondary"
            :aria-label="`Редактировать объект ${data.id}`"
          />
        </template>
      </Column>
      <template #empty>
        <div class="flex flex-col items-center justify-center gap-2 py-8 text-muted-color">
          <i class="pi pi-inbox text-2xl" aria-hidden="true" />
          <span>{{ loadError ? 'Список временно недоступен' : 'Объекты не найдены' }}</span>
        </div>
      </template>
    </DataTable>
  </section>
</template>
