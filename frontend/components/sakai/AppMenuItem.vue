<script setup lang="ts">
import { computed } from 'vue'
import { useSakaiLayout } from '~/composables/sakai/useSakaiLayout'

const props = defineProps<{
  item: {
    to: string
    label: string
    icon: string
  }
}>()

const route = useRoute()
const { hideMobileMenu } = useSakaiLayout()
const isActive = computed(() => route.path === props.item.to || route.path.startsWith(`${props.item.to}/`))
</script>

<template>
  <li>
    <NuxtLink
      :to="item.to"
      :class="{ 'active-route': isActive }"
      :aria-current="isActive ? 'page' : undefined"
      @click="hideMobileMenu"
    >
      <i :class="item.icon" class="layout-menuitem-icon" aria-hidden="true" />
      <span class="layout-menuitem-text">{{ item.label }}</span>
    </NuxtLink>
  </li>
</template>
