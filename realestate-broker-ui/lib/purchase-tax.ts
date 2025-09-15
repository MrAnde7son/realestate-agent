// Purchase tax calculation utilities for Israeli real estate transactions

export interface Buyer {
  share: number // percentage share in property (0-100)
  firstApartment: boolean
  oleh?: boolean
  disabled?: boolean
  bereavedFamily?: boolean
}

export interface VatData {
  rate: number
  lastUpdated: string
}

// Thresholds as of 2024 for residential purchase tax (NIS)
const FIRST_HOME_BRACKETS = [
  { upTo: 1978745, rate: 0 },
  { upTo: 2338195, rate: 0.035 },
  { upTo: 5062290, rate: 0.05 },
  { upTo: 17000000, rate: 0.08 },
  { upTo: Infinity, rate: 0.10 }
]

const ADDITIONAL_HOME_BRACKETS = [
  { upTo: 6055070, rate: 0.08 },
  { upTo: Infinity, rate: 0.10 }
]

// Reduced rate for special populations (oleh, disabled, bereaved families)
const SPECIAL_BRACKETS = [
  { upTo: 1978745, rate: 0.005 },
  { upTo: Infinity, rate: 0.05 }
]

function calcByBrackets(amount: number, brackets: { upTo: number; rate: number }[]): number {
  let tax = 0
  let prev = 0
  for (const b of brackets) {
    const taxable = Math.min(amount, b.upTo) - prev
    if (taxable > 0) {
      tax += taxable * b.rate
      prev = b.upTo
    }
  }
  return tax
}

// Calculate total purchase tax for all buyers
export function calculatePurchaseTax(price: number, buyers: Buyer[]): number {
  return buyers.reduce((sum, buyer) => {
    const sharePrice = price * (buyer.share / 100)
    const brackets = (buyer.oleh || buyer.disabled || buyer.bereavedFamily)
      ? SPECIAL_BRACKETS
      : buyer.firstApartment
        ? FIRST_HOME_BRACKETS
        : ADDITIONAL_HOME_BRACKETS
    return sum + calcByBrackets(sharePrice, brackets)
  }, 0)
}

// Fetch current VAT rate from Israel government data portal
export async function fetchVATRate(): Promise<VatData> {
  try {
    const res = await fetch('https://data.gov.il/api/3/action/datastore_search?resource_id=efad2e0b-b06f-4e6a-8a72-05dbeaab7ba6&limit=1')
    const json = await res.json()
    const record = json?.result?.records?.[0]
    const rate = parseFloat(record?.maam) || parseFloat(record?.Maam)
    const date = record?.date || record?.Date
    if (!isNaN(rate)) {
      return { rate: rate / 100, lastUpdated: date || new Date().toISOString() }
    }
  } catch (err) {
    console.error('Failed to fetch VAT rate', err)
  }
  return { rate: 0.17, lastUpdated: new Date().toISOString() }
}

export interface Fees {
  broker?: number
  lawyer?: number
  appraiser?: number
  renovation?: number
  furniture?: number
}

// Calculate total cost including fees and VAT
export function calculateTotalCost(price: number, tax: number, fees: Fees, vatRate: number): { total: number; feesWithVat: number } {
  const feesSum = (fees.broker || 0) + (fees.lawyer || 0) + (fees.appraiser || 0) + (fees.renovation || 0) + (fees.furniture || 0)
  const feesWithVat = feesSum * (1 + vatRate)
  return { total: price + tax + feesWithVat, feesWithVat }
}
