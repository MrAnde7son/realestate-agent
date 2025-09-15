export interface Buyer {
  name: string
  sharePct: number
  isFirstHome?: boolean
  isReplacementHome?: boolean
  oleh?: boolean
  disabled?: boolean
  bereavedFamily?: boolean
}

export interface PurchaseTaxBreakdown {
  buyer: Buyer
  portionPrice: number
  tax: number
  track: 'regular' | 'oleh' | 'disabled' | 'bereaved'
}

// 2025 single home brackets (freeze)
const SINGLE_HOME_BRACKETS = [
  { limit: 1_978_745, rate: 0 },
  { limit: 2_347_040, rate: 0.035 },
  { limit: 6_055_070, rate: 0.05 },
  { limit: 20_183_565, rate: 0.08 },
  { limit: Infinity, rate: 0.10 },
]

const ADDITIONAL_HOME_BRACKETS = [
  { limit: 6_055_070, rate: 0.08 },
  { limit: Infinity, rate: 0.10 },
]

const OLEH_BRACKETS = [
  { limit: 1_930_000, rate: 0.005 },
  { limit: Infinity, rate: 0.05 },
]

function applyBrackets(value: number, brackets: { limit: number; rate: number }[]): number {
  let tax = 0
  let prev = 0
  for (const b of brackets) {
    const taxable = Math.min(value, b.limit) - prev
    if (taxable > 0) tax += taxable * b.rate
    if (value <= b.limit) break
    prev = b.limit
  }
  return tax
}

function calcRegular(value: number, isFirst: boolean): number {
  const brackets = isFirst ? SINGLE_HOME_BRACKETS : ADDITIONAL_HOME_BRACKETS
  return applyBrackets(value, brackets)
}

function calcOleh(value: number): number {
  return applyBrackets(value, OLEH_BRACKETS)
}

function calcDisabled(value: number, isFirst: boolean): number {
  const cap = 2_500_000
  const reduced = Math.min(value, cap) * 0.005
  const remaining = value > cap ? calcRegular(value - cap, isFirst) : 0
  return reduced + remaining
}

const calcBereaved = calcDisabled

export function calculatePurchaseTax(price: number, buyers: Buyer[]): { totalTax: number; breakdown: PurchaseTaxBreakdown[] } {
  const breakdown = buyers.map((b) => {
    const portionPrice = (price * b.sharePct) / 100
    const isFirst = !!b.isFirstHome || !!b.isReplacementHome
    const regular = calcRegular(portionPrice, isFirst)
    const oleh = b.oleh ? calcOleh(portionPrice) : Infinity
    const disabled = b.disabled ? calcDisabled(portionPrice, isFirst) : Infinity
    const bereaved = b.bereavedFamily ? calcBereaved(portionPrice, isFirst) : Infinity
    const tax = Math.min(regular, oleh, disabled, bereaved)
    let track: 'regular' | 'oleh' | 'disabled' | 'bereaved' = 'regular'
    if (tax === oleh) track = 'oleh'
    else if (tax === disabled) track = 'disabled'
    else if (tax === bereaved) track = 'bereaved'
    return { buyer: b, portionPrice, tax, track }
  })
  const totalTax = breakdown.reduce((sum, b) => sum + b.tax, 0)
  return { totalTax, breakdown }
}
