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

export function calculateServiceCosts(
  price: number,
  services: ServiceInput[],
  vatRate: number
): { total: number; breakdown: ServiceCost[] } {
  const breakdown = services.reduce<ServiceCost[]>((acc, service) => {
    let cost = 0

    if (typeof service.amount === 'number' && service.amount > 0) {
      cost = service.amount
    } else if (typeof service.percent === 'number' && service.percent > 0) {
      cost = (price * service.percent) / 100
    }

    if (cost <= 0) {
      return acc
    }

    const includesVat = service.includesVat ?? false
    if (!includesVat) {
      cost = cost * (1 + vatRate)
    }

    acc.push({ label: service.label, cost })
    return acc
  }, [])

  const total = breakdown.reduce((sum, s) => sum + s.cost, 0)
  return { total, breakdown }
}
