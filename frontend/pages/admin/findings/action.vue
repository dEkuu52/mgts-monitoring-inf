<script setup lang="ts">
import { useRoute } from '#vue-router'
import { useRequest } from '~/services/useRequest'

definePageMeta({ name: 'findings-action', layout: 'admin' })

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
    const response = await useRequest(`/api/defects/${id.value}`)
    if (response.error) {
      await router.push('/admin/findings')
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
    const successMessage = isUpdateMode.value ? 'Дефект сохранён' : 'Дефект создан'
    const result = isUpdateMode.value
      ? await useRequest(`/api/defects/${id.value}`, { method: 'PUT', body: fields.value, successMessage, errorTitle: 'Не удалось сохранить дефект' })
      : await useRequest('/api/defects', { method: 'POST', body: fields.value, successMessage, errorTitle: 'Не удалось сохранить дефект' })

    if (result.error) {
      formError.value = result.error.description || 'Проверьте данные и попробуйте ещё раз.'
      return
    }

    await router.push('/admin/findings')
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
          <p class="text-muted-color text-xs font-semibold uppercase tracking-wide m-0">Результаты обработки</p>
          <h2 class="text-2xl font-semibold m-0">{{ isUpdateMode ? `Редактирование дефекта №${fields.id || id}` : 'Добавить дефект' }}</h2>
        </div>
      </template>
      <template #end>
        <Button label="К списку" icon="pi pi-arrow-left" severity="secondary" outlined as="router-link" to="/admin/findings" />
      </template>
    </Toolbar>

    <Message v-if="loading" severity="info" :closable="false">Загрузка данных дефекта…</Message>
    <Message v-if="formError" severity="error" :closable="false">{{ formError }}</Message>

    <div class="flex flex-col gap-4">
      <div class="flex flex-col gap-2">
        <label for="finding-detection">ID наблюдения</label>
        <InputText id="finding-detection" v-model="fields.detection_id" required class="w-full" />
      </div>
      <div class="flex flex-col gap-2">
        <label for="finding-type">Признак</label>
        <InputText id="finding-type" v-model="fields.defect_type" required class="w-full" />
      </div>
      <div class="flex flex-col gap-2">
        <label for="finding-confidence">Уверенность</label>
        <InputText id="finding-confidence" v-model="fields.defect_confidence" inputmode="decimal" class="w-full" />
      </div>
      <div class="flex flex-col gap-2">
        <label for="finding-severity">Критичность</label>
        <InputText id="finding-severity" v-model="fields.severity" class="w-full" />
      </div>
      <div class="flex flex-col gap-2">
        <label for="finding-action">Рекомендованное действие</label>
        <InputText id="finding-action" v-model="fields.recommended_action" class="w-full" />
      </div>
    </div>

    <div class="flex justify-end border-t border-surface-200 dark:border-surface-700 pt-4">
      <Button type="submit" :label="saving ? 'Сохранение…' : (isUpdateMode ? 'Сохранить изменения' : 'Создать дефект')" icon="pi pi-check" :loading="saving" :disabled="loading" />
    </div>
  </form>
</template>
