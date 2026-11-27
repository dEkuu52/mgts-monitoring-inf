/** Demo mode is opt-in: every other value keeps requests on the real API path. */
export function isDemoModeEnabled(value: unknown): boolean {
  return value === true || value === 'true'
}
