<script setup lang="ts">
import { useSakaiLayout } from '~/composables/sakai/useSakaiLayout'
import { computed } from 'vue'
import { findAdminSection } from './navigation'

const route = useRoute()
const { layoutConfig, toggleMenu, toggleDarkMode } = useSakaiLayout()
const currentSection = computed(() => findAdminSection(route.path))
</script>

<template>
  <header class="layout-topbar">
    <div class="layout-topbar-logo-container">
      <button
        type="button"
        class="layout-menu-button layout-topbar-action"
        aria-label="Переключить меню"
        @click="toggleMenu"
      >
        <i class="pi pi-bars" aria-hidden="true" />
      </button>
      <NuxtLink class="layout-topbar-logo" to="/admin/objects">
        <i class="pi pi-building" aria-hidden="true" />
        <span>МГТС</span>
      </NuxtLink>
    </div>

    <span class="hidden md:inline text-muted-color font-semibold">
      {{ currentSection?.label || 'Мониторинг инфраструктуры' }}
    </span>

    <div class="layout-topbar-actions">
      <button
        type="button"
        class="layout-topbar-action"
        :aria-label="layoutConfig.darkTheme ? 'Включить светлую тему' : 'Включить тёмную тему'"
        @click="toggleDarkMode"
      >
        <i :class="['pi', layoutConfig.darkTheme ? 'pi-sun' : 'pi-moon']" aria-hidden="true" />
      </button>
    </div>
  </header>
</template>
