export default {
    port: 3001,
    // Адрес нужен только для прямых запросов мимо Nitro-прокси.
    // Основной канал — относительные пути /api/* через прокси Nuxt.
    apiUrl: "http://localhost:3001/api",
    apiPrefix: "/api/",
    // false — фронтенд работает с реальным FastAPI-бэкендом.
    // true — локальные моки из services/mockApi.ts (например, без поднятого API).
    useMocks: false
}
