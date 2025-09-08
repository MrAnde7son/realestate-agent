export interface OnboardingState {
  connectPayment: boolean
  addAsset: boolean
  generateReport: boolean
  createAlert: boolean
}

export function selectOnboardingState(user: any): OnboardingState {
  const flags = user?.onboarding_flags || {}
  const state = {
    connectPayment: Boolean(flags.connect_payment),
    addAsset: Boolean(flags.add_first_asset),
    generateReport: Boolean(flags.generate_first_report),
    createAlert: Boolean(flags.set_one_alert),
  }
  
  
  return state
}

export function getCompletionPct(state: OnboardingState): number {
  // Only count the active steps (exclude connectPayment as it's commented out in UI)
  const activeSteps = {
    addAsset: state.addAsset,
    generateReport: state.generateReport,
    createAlert: state.createAlert,
  }
  const values = Object.values(activeSteps)
  const completed = values.filter(Boolean).length
  return Math.round((completed / values.length) * 100)
}
