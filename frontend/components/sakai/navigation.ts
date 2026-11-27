export const adminNavigation = [
  { to: '/admin/users', label: 'Пользователи', icon: 'pi pi-fw pi-users' },
  { to: '/admin/objects', label: 'Объекты', icon: 'pi pi-fw pi-box' },
  { to: '/admin/findings', label: 'Дефекты', icon: 'pi pi-fw pi-exclamation-triangle' },
  { to: '/admin/statuses', label: 'Статусы', icon: 'pi pi-fw pi-tag' },
  { to: '/admin/map', label: 'Карта', icon: 'pi pi-fw pi-map' },
]

export function findAdminSection(path: string) {
  return adminNavigation.find(item => path === item.to || path.startsWith(`${item.to}/`))
}
