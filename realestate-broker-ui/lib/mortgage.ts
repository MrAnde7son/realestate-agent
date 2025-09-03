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

// Fallback Bank of Israel rate in case API call fails
const DEFAULT_BOI_RATE = 4.5

// Generate mortgage scenarios based on a given base rate
export function getMortgageScenarios(baseRate: number): MortgageScenario[] {
  return [
    {
      name: "בנק לאומי - קבוע",
      description: "ריבית קבועה למשך כל תקופת ההלוואה",
      baseRate,
      bankMargin: 1.8,
      totalRate: baseRate + 1.8
    },
    {
      name: "בנק הפועלים - משתנה",
      description: "ריבית משתנה בהתאם לשינויי בנק ישראל",
      baseRate,
      bankMargin: 1.5,
      totalRate: baseRate + 1.5
    },
    {
      name: "מזרחי טפחות - פריים",
      description: "מסלול פריים - ריבית משתנה עם מרווח נמוך",
      baseRate,
      bankMargin: 1.3,
      totalRate: baseRate + 1.3
    }
  ]
}

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

export function calculateAllScenarios(input: MortgageInput, baseRate: number): MortgageCalculation[] {
  return getMortgageScenarios(baseRate).map(scenario => calculateMortgage(input, scenario))
}

// Fetch current Bank of Israel interest rate and last update date
export interface BOIRateData {
  baseRate: number
  lastUpdated: string
}

export async function fetchBOIRate(): Promise<BOIRateData> {
  try {
    const res = await fetch('https://www.boi.org.il/PublicApi/GetInterest')
    const data = await res.json()
    const rate = data?.currentInterest
    const nextDate = data?.nextInterestDate

    if (typeof rate === 'number') {
      return {
        baseRate: rate,
        lastUpdated: nextDate || new Date().toISOString()
      }
    }

    throw new Error('Invalid data from Bank of Israel')
  } catch (error) {
    console.error('Error fetching BOI rate:', error)
    return {
      baseRate: DEFAULT_BOI_RATE,
      lastUpdated: new Date().toISOString()
    }
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
