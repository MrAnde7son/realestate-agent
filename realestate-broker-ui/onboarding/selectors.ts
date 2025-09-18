export interface OnboardingState {
  connectPayment: boolean
  addAsset: boolean
  generateReport: boolean
  createAlert: boolean
}

export function selectOnboardingState(user: any): OnboardingState {
  // If user is null or undefined, return default state (all false)
  if (!user) {
    return {
      connectPayment: false,
      addAsset: false,
      generateReport: false,
      createAlert: false,
    }
  }
  
  const flags = user.onboarding_flags || {}
  const state = {
    connectPayment: Boolean(flags.connect_payment),
    addAsset: Boolean(flags.add_first_asset),
    generateReport: Boolean(flags.generate_first_report),
    createAlert: Boolean(flags.set_one_alert),
  }
  
  return state
}

export function getCompletionPct(state: OnboardingState): number {
  // Count all steps that are actually shown in the UI
  // Note: connectPayment is commented out in the UI components, so we exclude it
  const activeSteps = {
    addAsset: state.addAsset,
    generateReport: state.generateReport,
    createAlert: state.createAlert,
  }
  const values = Object.values(activeSteps)
  const completed = values.filter(Boolean).length
  return Math.round((completed / values.length) * 100)
}

export function isOnboardingComplete(state: OnboardingState): boolean {
  // Use the same logic as the backend - all steps must be completed
  // Since connectPayment is commented out in UI but still required by backend,
  // we need to check if the visible steps are complete AND if we should show the components
  const visibleSteps = {
    addAsset: state.addAsset,
    generateReport: state.generateReport,
    createAlert: state.createAlert,
  }
  
  const isComplete = Object.values(visibleSteps).every(Boolean)
  
  // For UI purposes, consider onboarding complete when all visible steps are done
  // The backend will still track connectPayment separately
  return isComplete
}
