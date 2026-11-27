<script setup lang="ts">
import AppMenuItem from './AppMenuItem.vue'
import { adminNavigation } from './navigation'
</script>

<template>
  <nav aria-label="Основная навигация">
    <ul class="layout-menu">
      <li class="layout-root-menuitem">
        <div class="layout-menuitem-root-text">Рабочая область</div>
        <ul class="layout-submenu">
          <AppMenuItem
            v-for="item in adminNavigation"
            :key="item.to"
            :item="item"
          />
        </ul>
      </li>
    </ul>
  </nav>
</template>
