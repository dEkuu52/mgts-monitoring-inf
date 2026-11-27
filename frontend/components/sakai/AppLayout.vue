<script setup lang="ts">
import { computed, watch } from 'vue'
import { useSakaiLayout } from '~/composables/sakai/useSakaiLayout'
import AppFooter from './AppFooter.vue'
import AppSidebar from './AppSidebar.vue'
import AppTopbar from './AppTopbar.vue'

const route = useRoute()
const { layoutConfig, layoutState, hideMobileMenu } = useSakaiLayout()

const containerClass = computed(() => ({
  'layout-overlay': false,
  'layout-static': layoutConfig.value.menuMode === 'static',
  'layout-overlay-active': false,
  'layout-mobile-active': layoutState.value.mobileMenuActive,
  'layout-static-inactive': layoutState.value.staticMenuInactive,
}))

watch(() => route.path, hideMobileMenu)
</script>

<template>
  <div class="layout-wrapper" :class="containerClass">
    <AppTopbar />
    <AppSidebar />
    <div class="layout-main-container">
      <main class="layout-main">
        <slot />
      </main>
      <AppFooter />
    </div>
    <div class="layout-mask" aria-hidden="true" @click="hideMobileMenu" />
  </div>
</template>
