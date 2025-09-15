export interface ServiceInput {
  percent?: number
  amount?: number
  includesVat?: boolean
  label: string
}

export interface ServiceCost {
  label: string
  cost: number
}

export function calculateServiceCosts(price: number, services: ServiceInput[], vatRate: number): { total: number; breakdown: ServiceCost[] } {
  const breakdown = services.map((s) => {
    let cost = 0
    if (typeof s.amount === 'number' && s.amount > 0) {
      cost = s.amount
    } else if (typeof s.percent === 'number' && s.percent > 0) {
      cost = (price * s.percent) / 100
    }
    if (!s.includesVat) {
      cost = cost * (1 + vatRate)
    }
    return { label: s.label, cost }
  })
  const total = breakdown.reduce((sum, s) => sum + s.cost, 0)
  return { total, breakdown }
}
