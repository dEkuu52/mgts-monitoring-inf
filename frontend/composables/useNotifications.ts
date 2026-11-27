type ToastApi = {
  success: (options: Record<string, unknown>) => void
  error: (options: Record<string, unknown>) => void
}

/**
 * Тост-уведомления доступны только в браузере: на SSR приложение
 * не должно пытаться рисовать DOM-элементы izitoast.
 */
function resolveToast(): ToastApi | null {
  if (!import.meta.client) return null

  try {
    return useToast() as ToastApi
  }
  catch {
    // На случай вызова вне Nuxt-контекста (например, из фонового колбэка).
  }

  try {
    return (useNuxtApp() as unknown as { $iziToast?: ToastApi }).$iziToast || null
  }
  catch {
    return null
  }
}

export function useNotifications() {
  const toast = resolveToast()

  return {
    success(message: string, title = 'Готово') {
      toast?.success({ title, message, timeout: 3000 })
    },
    error(message: string, title = 'Ошибка') {
      toast?.error({ title, message, timeout: 5000 })
    },
  }
}
