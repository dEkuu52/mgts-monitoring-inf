<script setup lang="ts">
import { useRoute } from '#vue-router'
import { useRequest } from '~/services/useRequest'

definePageMeta({ name: 'statuses-action', layout: 'admin' })

const router = useRouter()
const route = useRoute()
const id = computed(() => route.query?.id)
const isUpdateMode = computed(() => !!id.value)
const fields = ref<Record<string, any>>({})
const loading = ref(false)
const saving = ref(false)
const formError = ref('')

async function getData() {
  loading.value = true
  try {
    const response = await useRequest(`/api/statuses/${id.value}`)
    if (response.error) {
      await router.push('/admin/statuses')
      return
    }
    fields.value = response.data || {}
  } finally {
    loading.value = false
  }
}

async function sendData() {
  if (saving.value) return
  saving.value = true
  formError.value = ''

  try {
    const successMessage = isUpdateMode.value ? 'Статус сохранён' : 'Статус создан'
    const result = isUpdateMode.value
      ? await useRequest(`/api/statuses/${id.value}`, { method: 'PUT', body: fields.value, successMessage, errorTitle: 'Не удалось сохранить статус' })
      : await useRequest('/api/statuses', { method: 'POST', body: fields.value, successMessage, errorTitle: 'Не удалось сохранить статус' })

    if (result.error) {
      formError.value = result.error.description || 'Проверьте данные и попробуйте ещё раз.'
      return
    }

    await router.push('/admin/statuses')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  if (isUpdateMode.value) getData()
})
</script>

<template>
  <form class="card flex flex-col gap-6 max-w-3xl" @submit.prevent="sendData">
    <Toolbar>
      <template #start>
        <div>
          <p class="text-muted-color text-xs font-semibold uppercase tracking-wide m-0">Справочник</p>
          <h2 class="text-2xl font-semibold m-0">{{ isUpdateMode ? `Редактирование статуса №${fields.id || id}` : 'Добавить статус' }}</h2>
        </div>
      </template>
      <template #end>
        <Button label="К списку" icon="pi pi-arrow-left" severity="secondary" outlined as="router-link" to="/admin/statuses" />
      </template>
    </Toolbar>

    <Message v-if="loading" severity="info" :closable="false">Загрузка статуса…</Message>
    <Message v-if="formError" severity="error" :closable="false">{{ formError }}</Message>

    <div class="flex flex-col gap-4">
      <div class="flex flex-col gap-2">
        <label for="status-type">Тип</label>
        <InputText id="status-type" v-model="fields.type" required class="w-full" />
      </div>
      <div class="flex flex-col gap-2">
        <label for="status-description">Описание</label>
        <Textarea id="status-description" v-model="fields.description" rows="5" auto-resize class="w-full" />
      </div>
    </div>

    <div class="flex justify-end border-t border-surface-200 dark:border-surface-700 pt-4">
      <Button type="submit" :label="saving ? 'Сохранение…' : (isUpdateMode ? 'Сохранить изменения' : 'Создать статус')" icon="pi pi-check" :loading="saving" :disabled="loading" />
    </div>
  </form>
</template>
