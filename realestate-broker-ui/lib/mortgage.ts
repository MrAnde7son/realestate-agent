// Mortgage calculation utilities with Bank of Israel interest rates

export interface MortgageScenario {
  name: string
  description: string
  baseRate: number // Bank of Israel base rate
  bankMargin: number // Bank margin above base rate
  totalRate: number // Total interest rate
}

export interface MortgageCalculation {
  monthlyPayment: number
  totalPayment: number
  totalInterest: number
  scenario: MortgageScenario
}

export interface MortgageInput {
  loanAmount: number
  loanTermYears: number
  propertyValue: number
}

// Mock Bank of Israel current interest rate (in real implementation, this would be fetched from BOI API)
const CURRENT_BOI_RATE = 4.75 // Current base rate as of latest update

// Three mortgage scenarios based on different banks and loan terms
export const MORTGAGE_SCENARIOS: MortgageScenario[] = [
  {
    name: "בנק לאומי - קבוע",
    description: "ריבית קבועה למשך כל תקופת ההלוואה",
    baseRate: CURRENT_BOI_RATE,
    bankMargin: 1.8,
    totalRate: CURRENT_BOI_RATE + 1.8
  },
  {
    name: "בנק הפועלים - משתנה",
    description: "ריבית משתנה בהתאם לשינויי בנק ישראל",
    baseRate: CURRENT_BOI_RATE,
    bankMargin: 1.5,
    totalRate: CURRENT_BOI_RATE + 1.5
  },
  {
    name: "מזרחי טפחות - פריים",
    description: "מסלול פריים - ריבית משתנה עם מרווח נמוך",
    baseRate: CURRENT_BOI_RATE,
    bankMargin: 1.3,
    totalRate: CURRENT_BOI_RATE + 1.3
  }
]

export function calculateMortgage(input: MortgageInput, scenario: MortgageScenario): MortgageCalculation {
  const { loanAmount, loanTermYears } = input
  const monthlyRate = scenario.totalRate / 100 / 12
  const numberOfPayments = loanTermYears * 12
  
  // Calculate monthly payment using standard mortgage formula
  const monthlyPayment = loanAmount * 
    (monthlyRate * Math.pow(1 + monthlyRate, numberOfPayments)) / 
    (Math.pow(1 + monthlyRate, numberOfPayments) - 1)
  
  const totalPayment = monthlyPayment * numberOfPayments
  const totalInterest = totalPayment - loanAmount
  
  return {
    monthlyPayment,
    totalPayment,
    totalInterest,
    scenario
  }
}

export function calculateAllScenarios(input: MortgageInput): MortgageCalculation[] {
  return MORTGAGE_SCENARIOS.map(scenario => calculateMortgage(input, scenario))
}

// Function to fetch current Bank of Israel interest rate (for future implementation)
export async function fetchBOIRate(): Promise<number> {
  try {
    // In real implementation, this would call Bank of Israel API
    // For now, return the current known rate
    return CURRENT_BOI_RATE
  } catch (error) {
    console.error('Error fetching BOI rate:', error)
    return CURRENT_BOI_RATE // Fallback to current rate
  }
}

// Helper function to calculate loan-to-value ratio
export function calculateLTV(loanAmount: number, propertyValue: number): number {
  return (loanAmount / propertyValue) * 100
}

// Helper function to calculate affordability based on income
export function calculateAffordability(monthlyIncome: number, monthlyPayment: number): {
  ratio: number
  isAffordable: boolean
} {
  const ratio = (monthlyPayment / monthlyIncome) * 100
  const isAffordable = ratio <= 30 // Standard affordability ratio
  
  return { ratio, isAffordable }
}
