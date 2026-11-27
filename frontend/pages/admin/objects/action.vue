<script setup lang="ts">
import {useRoute} from "#vue-router";
import {useRequest} from "~/services/useRequest";
import {useNotifications} from "~/composables/useNotifications";

definePageMeta({
  name: 'objects-action',
  layout: 'admin'
})

const MAX_PHOTO_SIZE = 5 * 1024 * 1024
const ALLOWED_PHOTO_TYPES = ['image/jpeg', 'image/png', 'image/webp']
const ALLOWED_PHOTO_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp']

const PROCESSING_LABELS: Record<string, string> = {
  awaiting_processing: 'Ожидает обработки',
  awating_processing: 'Ожидает обработки',
  pending: 'Ожидает обработки',
  processing: 'Обрабатывается',
  done: 'Обработано',
  failed: 'Ошибка обработки'
}

const $router = useRouter()
const $route = useRoute()
const notifications = useNotifications()

const id = computed(() => $route.query?.id)

const isUpdateMode = computed(() => !!id.value)

const fields = ref<Record<string, any>>({})
const statuses = ref<Record<string, any>[]>([])
const statusOptions = computed(() => [
  { label: 'Статус не выбран', value: null },
  ...statuses.value.map(status => ({
    label: `${status.type}${status.description ? ` — ${status.description}` : ''}`,
    value: status.id,
  })),
])
const loading = ref(false)
const saving = ref(false)
const formError = ref('')

const photoInput = ref<HTMLInputElement | null>(null)
const photoFile = ref<File | null>(null)
const photoPreview = ref<string | null>(null)
const photoRemoved = ref(false)
// Оверлей на всю страницу показываем только во время перетаскивания файла.
const isDragging = ref(false)
const dragDepth = ref(0)
// Прибавляется после загрузки нового фото, чтобы превью не показало старую версию из кэша.
const photoVersion = ref(0)

const hasSavedPhoto = computed(() => !!fields.value?.img_url)

const photoUrl = computed(() => {
  const url = fields.value?.img_url

  if (!url) return null
  if (!photoVersion.value) return url

  const separator = url.includes('?') ? '&' : '?'
  return `${url}${separator}v=${photoVersion.value}`
})

const previewUrl = computed(() => photoPreview.value || photoUrl.value)

const processedPhotoUrl = computed(() => fields.value?.processed_img_url || null)

const processingLabel = computed(() => {
  const status = fields.value?.processing_status
  return status ? (PROCESSING_LABELS[status] || status) : ''
})

const processingError = computed(() => fields.value?.processing_error || '')

function releasePreview() {
  if (photoPreview.value) {
    URL.revokeObjectURL(photoPreview.value)
    photoPreview.value = null
  }
}

// Общая проверка файла — используется и для выбора через диалог, и для drag-and-drop.
function acceptPhotoFile(file: File) {
  formError.value = ''

  const extension = file.name.split('.').pop()?.toLowerCase() || ''
  const isAllowedType = ALLOWED_PHOTO_TYPES.includes(file.type)
    || ALLOWED_PHOTO_EXTENSIONS.includes(extension)

  if (!isAllowedType) {
    formError.value = 'Допустимы только изображения JPEG, PNG и WebP.'
    notifications.error(formError.value, 'Неподдерживаемый файл')
    if (photoInput.value) photoInput.value.value = ''
    return
  }

  if (file.size > MAX_PHOTO_SIZE) {
    formError.value = 'Максимальный размер фото — 5 МБ.'
    notifications.error(formError.value, 'Слишком большой файл')
    if (photoInput.value) photoInput.value.value = ''
    return
  }

  releasePreview()
  photoFile.value = file
  photoPreview.value = URL.createObjectURL(file)
  photoRemoved.value = false
}

function onPhotoSelected(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0] || null

  if (!file) return

  acceptPhotoFile(file)
}

function openFileDialog() {
  photoInput.value?.click()
}

function hasDraggedFiles(event: DragEvent) {
  return !!event.dataTransfer?.types.includes('Files')
}

// Слушатели висят на window: файл можно бросить в любое место страницы.
// Счётчик нужен, чтобы оверлей не мигал при переходе между элементами.
function onWindowDragEnter(event: DragEvent) {
  if (!hasDraggedFiles(event)) return

  event.preventDefault()
  dragDepth.value += 1
  isDragging.value = true
}

function onWindowDragOver(event: DragEvent) {
  if (!hasDraggedFiles(event)) return

  event.preventDefault()
  if (event.dataTransfer) event.dataTransfer.dropEffect = 'copy'
  isDragging.value = true
}

function onWindowDragLeave(event: DragEvent) {
  if (!isDragging.value) return

  dragDepth.value = Math.max(0, dragDepth.value - 1)
  if (dragDepth.value === 0 || !event.relatedTarget) {
    dragDepth.value = 0
    isDragging.value = false
  }
}

function onWindowDrop(event: DragEvent) {
  event.preventDefault()
  dragDepth.value = 0
  isDragging.value = false

  const file = event.dataTransfer?.files?.[0]
  if (file) acceptPhotoFile(file)
}

function markPhotoForRemoval() {
  releasePreview()
  photoFile.value = null
  photoRemoved.value = true

  if (photoInput.value) {
    photoInput.value.value = ''
  }
}

function cancelPhotoRemoval() {
  photoRemoved.value = false
}

async function getStatuses() {
  const response = await useRequest('/api/statuses')

  if (!response.error && Array.isArray(response.data)) {
    statuses.value = response.data
  }
}

async function getData() {
  loading.value = true

  try {
    const response = await useRequest(`/api/infrastructure-objects/${id.value}`)

    if (!!response.error) {
      await $router.push("/admin/objects");
      return;
    }

    fields.value = response.data || {}
  } finally {
    loading.value = false
  }
}

function buildPayload() {
  // В PUT отправляем только поля, которые принимает бэкенд.
  const source = fields.value || {}

  return {
    type: source.type,
    external_id: source.external_id,
    place: source.place,
    lat: source.lat,
    lon: source.lon,
    status_id: source.status_id,
  }
}

async function uploadPhoto(objectId: string | number) {
  if (!photoFile.value) return null

  const formData = new FormData()
  formData.append('file', photoFile.value)

  return useRequest(`/api/infrastructure-objects/${objectId}/photo`, {
    method: 'POST',
    body: formData,
    successMessage: 'Фото загружено',
    errorTitle: 'Не удалось загрузить фото',
  })
}

async function sendData() {
  if (saving.value) return

  saving.value = true
  formError.value = ''

  try {
    const payload = buildPayload()
    // Если вместе с объектом сохраняется фото, итоговый тост покажет
    // результат загрузки/удаления фото, чтобы не было двух «успехов» подряд.
    const saveSuccessMessage = (photoFile.value || photoRemoved.value)
      ? false
      : (isUpdateMode.value ? 'Объект сохранён' : 'Объект создан')

    const result = isUpdateMode.value
      ? await useRequest(`/api/infrastructure-objects/${id.value}`, {
        method: 'PUT',
        body: payload,
        successMessage: saveSuccessMessage,
        errorTitle: 'Не удалось сохранить объект',
      })
      : await useRequest(`/api/infrastructure-objects`, {
        method: 'POST',
        body: payload,
        successMessage: saveSuccessMessage,
        errorTitle: 'Не удалось создать объект',
      })

    if (!!result.error) {
      formError.value = [result.error.title, result.error.description]
        .filter(Boolean)
        .join('. ')
      return
    }

    const saved = result.data || {}
    const savedId = saved.id || id.value

    if (!savedId) {
      formError.value = 'Объект сохранён, но сервер не вернул его ID.'
      return
    }

    if (photoFile.value) {
      const uploadResult = await uploadPhoto(savedId)

      if (!!uploadResult?.error) {
        // Объект уже сохранён — переводим форму в режим редактирования,
        // чтобы фото можно было прикрепить повторно.
        fields.value = {...saved, ...(uploadResult.data || {})}
        if (!isUpdateMode.value) {
          await $router.replace({path: '/admin/objects/action', query: {id: savedId}})
        }
        formError.value = `Объект сохранён, но фото загрузить не удалось: ${uploadResult.error.title}. ${uploadResult.error.description || ''}`.trim()
        return
      }

      photoFile.value = null
      releasePreview()
      photoRemoved.value = false
      photoVersion.value = Date.now()
      fields.value = {...saved, ...(uploadResult?.data || {})}
    } else if (photoRemoved.value && hasSavedPhoto.value) {
      const removeResult = await useRequest(`/api/infrastructure-objects/${savedId}/photo`, {
        method: 'DELETE',
        successMessage: 'Фото удалено',
        errorTitle: 'Не удалось удалить фото',
      })

      if (!!removeResult.error) {
        if (!isUpdateMode.value) {
          await $router.replace({path: '/admin/objects/action', query: {id: savedId}})
        }
        formError.value = `Объект сохранён, но фото удалить не удалось: ${removeResult.error.title}. ${removeResult.error.description || ''}`.trim()
        return
      }

      photoRemoved.value = false
      fields.value = {...saved, ...(removeResult.data || {}), img_url: null, processed_img_url: null}
    }

    await $router.push("/admin/objects");
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  getStatuses()

  if (isUpdateMode.value) {
    getData()
  }

  window.addEventListener('dragenter', onWindowDragEnter)
  window.addEventListener('dragover', onWindowDragOver)
  window.addEventListener('dragleave', onWindowDragLeave)
  window.addEventListener('drop', onWindowDrop)
})

onBeforeUnmount(() => {
  releasePreview()

  window.removeEventListener('dragenter', onWindowDragEnter)
  window.removeEventListener('dragover', onWindowDragOver)
  window.removeEventListener('dragleave', onWindowDragLeave)
  window.removeEventListener('drop', onWindowDrop)
})
</script>

<template>
  <form class="card flex flex-col gap-6" @submit.prevent="sendData">
    <Toolbar>
      <template #start>
        <div>
          <p class="text-muted-color text-xs font-semibold uppercase tracking-wide m-0">Реестр инфраструктуры</p>
          <h2 class="text-2xl font-semibold m-0">{{ isUpdateMode ? `Объект №${fields.id || id}` : 'Добавить объект' }}</h2>
        </div>
      </template>
      <template #end>
        <Button label="К списку" icon="pi pi-arrow-left" severity="secondary" outlined as="router-link" to="/admin/objects" />
      </template>
    </Toolbar>

    <Message v-if="loading" severity="info" :closable="false">Загрузка данных объекта…</Message>
    <Message v-if="formError" severity="error" :closable="false">{{ formError }}</Message>

    <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
      <div class="flex flex-col gap-2">
        <label for="object-type">Тип объекта</label>
        <InputText id="object-type" v-model="fields.type" required class="w-full" />
      </div>
      <div class="flex flex-col gap-2">
        <label for="object-external-id">Внешний идентификатор</label>
        <InputText id="object-external-id" v-model="fields.external_id" class="w-full" />
      </div>
      <div class="flex flex-col gap-2 md:col-span-2">
        <label for="object-place">Место</label>
        <InputText id="object-place" v-model="fields.place" class="w-full" />
      </div>
      <div class="flex flex-col gap-2">
        <label for="object-lat">Широта</label>
        <InputText id="object-lat" v-model="fields.lat" inputmode="decimal" class="w-full" />
      </div>
      <div class="flex flex-col gap-2">
        <label for="object-lon">Долгота</label>
        <InputText id="object-lon" v-model="fields.lon" inputmode="decimal" class="w-full" />
      </div>
      <div class="flex flex-col gap-2 md:col-span-2">
        <label for="object-status">Статус</label>
        <Select
          v-if="statuses.length"
          input-id="object-status"
          v-model="fields.status_id"
          :options="statusOptions"
          option-label="label"
          option-value="value"
          placeholder="Выберите статус"
          class="w-full"
        />
        <InputText v-else id="object-status" v-model="fields.status_id" placeholder="ID статуса" class="w-full" />
      </div>
    </div>

    <section class="flex flex-col gap-4 border-t border-surface-200 dark:border-surface-700 pt-6" aria-labelledby="object-photo-heading">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p class="text-muted-color text-xs font-semibold uppercase tracking-wide m-0">Изображение</p>
          <h3 id="object-photo-heading" class="text-xl font-semibold m-0">Фото объекта</h3>
        </div>
        <Tag v-if="processingLabel" :value="processingLabel" :severity="fields.processing_status === 'failed' ? 'danger' : fields.processing_status === 'done' ? 'success' : 'warn'" />
      </div>
      <p class="text-sm text-muted-color max-w-prose m-0">
        JPEG, PNG или WebP, не больше 5 МБ. Одно фото на объект — новое заменит предыдущее.
        Файл можно перетащить в любое место страницы.
      </p>

      <div class="grid grid-cols-1 items-start gap-6 lg:grid-cols-[minmax(14rem,22.5rem)_minmax(0,1fr)]">
        <div v-if="previewUrl" class="flex flex-col gap-3 rounded-lg border border-surface-200 dark:border-surface-700 p-4">
          <Image :src="previewUrl" alt="Фото объекта" image-class="w-full max-h-72 object-contain rounded-lg" preview />
          <div class="flex flex-wrap items-center justify-between gap-2 text-sm text-muted-color">
            <span>{{ photoFile ? 'Предпросмотр выбранного файла' : 'Текущее фото объекта' }}</span>
            <Tag v-if="photoRemoved" value="Будет удалено после сохранения" severity="warn" />
          </div>
        </div>
        <div v-else class="flex min-h-56 flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-surface-300 dark:border-surface-600 p-6 text-center text-sm text-muted-color">
          <i class="pi pi-image text-2xl text-primary" aria-hidden="true" />
          <strong class="font-semibold text-color">Фото не загружено</strong>
          <span>Добавьте изображение, чтобы оно было связано с объектом.</span>
        </div>

        <div class="flex flex-col items-start gap-3">
          <Button
            :label="previewUrl ? 'Выбрать другое фото' : 'Прикрепить фото'"
            :icon="previewUrl ? 'pi pi-refresh' : 'pi pi-upload'"
            type="button"
            outlined
            @click="openFileDialog"
          />
          <Button
            v-if="previewUrl && !photoRemoved"
            label="Удалить фото"
            icon="pi pi-trash"
            type="button"
            severity="danger"
            text
            @click="markPhotoForRemoval"
          />
          <Button
            v-else-if="photoRemoved && hasSavedPhoto"
            label="Отменить удаление"
            icon="pi pi-undo"
            type="button"
            severity="secondary"
            text
            @click="cancelPhotoRemoval"
          />
          <input
            id="object-photo"
            ref="photoInput"
            class="sr-only"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            aria-label="Выберите фото объекта"
            @change="onPhotoSelected"
          />
          <span v-if="photoFile" class="break-all text-sm text-muted-color">Выбрано: {{ photoFile.name }}</span>
        </div>
      </div>

      <Message v-if="processingError" severity="error" :closable="false">
        Ошибка обработки: {{ processingError }}
      </Message>

      <div v-if="processedPhotoUrl" class="grid grid-cols-1 items-start gap-6 border-t border-surface-200 dark:border-surface-700 pt-6 lg:grid-cols-[minmax(0,1fr)_minmax(14rem,22.5rem)]">
        <div>
          <p class="text-muted-color text-xs font-semibold uppercase tracking-wide m-0">Результат обработки</p>
          <h4 class="text-lg font-semibold m-0">Аннотированное изображение</h4>
        </div>
        <a :href="processedPhotoUrl" target="_blank" rel="noopener noreferrer" aria-label="Открыть аннотированное изображение">
          <Image :src="processedPhotoUrl" alt="Аннотированное изображение объекта" image-class="w-full max-h-72 object-contain rounded-lg border border-surface-200 dark:border-surface-700 bg-surface-50 dark:bg-surface-900" preview />
        </a>
      </div>
    </section>

    <div class="flex justify-end border-t border-surface-200 dark:border-surface-700 pt-4">
      <Button type="submit" :label="saving ? 'Сохранение…' : (isUpdateMode ? 'Сохранить изменения' : 'Создать объект')" icon="pi pi-check" :loading="saving" :disabled="loading" />
    </div>
  </form>

  <Teleport to="body">
    <div v-if="isDragging" class="fixed inset-0 z-[1000] flex flex-col items-center justify-center gap-4 border-2 border-dashed border-primary bg-surface-0/90 dark:bg-surface-950/90 text-color pointer-events-none text-lg font-semibold" role="status">
      <i class="pi pi-cloud-upload text-3xl text-primary" aria-hidden="true" />
      <span>Отпустите изображение, чтобы прикрепить фото</span>
    </div>
  </Teleport>
</template>
