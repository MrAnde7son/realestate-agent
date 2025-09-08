export interface OnboardingState {
  connectPayment: boolean
  addAsset: boolean
  generateReport: boolean
  createAlert: boolean
}

export function selectOnboardingState(user: any): OnboardingState {
  const flags = user?.onboarding_flags || {}
  return {
    connectPayment: Boolean(flags.connect_payment),
    addAsset: Boolean(flags.add_first_asset),
    generateReport: Boolean(flags.generate_first_report),
    createAlert: Boolean(flags.set_one_alert),
  }
}

export function getCompletionPct(state: OnboardingState): number {
  const values = Object.values(state)
  const completed = values.filter(Boolean).length
  return Math.round((completed / values.length) * 100)
}
