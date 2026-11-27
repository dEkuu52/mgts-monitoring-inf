interface SakaiLayoutConfig {
  darkTheme: boolean
  menuMode: 'static'
}

interface SakaiLayoutState {
  staticMenuInactive: boolean
  mobileMenuActive: boolean
}

export function useSakaiLayout() {
  const layoutConfig = useState<SakaiLayoutConfig>('sakai:layout-config', () => ({
    darkTheme: false,
    menuMode: 'static',
  }))
  const layoutState = useState<SakaiLayoutState>('sakai:layout-state', () => ({
    staticMenuInactive: false,
    mobileMenuActive: false,
  }))

  function isDesktop() {
    return import.meta.client && window.innerWidth > 991
  }

  function toggleMenu() {
    if (isDesktop()) {
      layoutState.value.staticMenuInactive = !layoutState.value.staticMenuInactive
      return
    }

    layoutState.value.mobileMenuActive = !layoutState.value.mobileMenuActive
  }

  function hideMobileMenu() {
    layoutState.value.mobileMenuActive = false
  }

  function toggleDarkMode() {
    if (!import.meta.client) return

    layoutConfig.value.darkTheme = !layoutConfig.value.darkTheme
    document.documentElement.classList.toggle('app-dark', layoutConfig.value.darkTheme)
  }

  return {
    layoutConfig,
    layoutState,
    isDesktop,
    toggleMenu,
    hideMobileMenu,
    toggleDarkMode,
  }
}
