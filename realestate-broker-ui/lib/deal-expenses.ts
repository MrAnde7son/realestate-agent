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

export interface BuildCostEstimate {
  breakdown: Record<string, {
    cost_per_sqm: number
    total_cost: number
    area_m2: number
  }>
  totals: {
    base_cost: number
    base_cost_with_vat: number
    low_cost: number
    low_cost_with_vat: number
    high_cost: number
    high_cost_with_vat: number
  }
  metadata: {
    area_m2: number
    region: string
    quality: string
    scope: string[]
    base_cost_per_sqm: number
    vat_rate: number
  }
}

export interface CostEstimateOptions {
  regions: Array<{ code: string; name: string }>
  qualities: Array<{ code: string; name: string }>
  scopes: Array<{ code: string; name: string }>
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

export function mergeBuildEstimateIntoDeal(
  expenses: any,
  buildEstimate: BuildCostEstimate,
  estimateType: 'low' | 'base' | 'high' = 'base'
): any {
  const estimateKey = estimateType === 'low' ? 'low_cost_with_vat' : 
                     estimateType === 'high' ? 'high_cost_with_vat' : 
                     'base_cost_with_vat'
  
  const estimatedCost = buildEstimate.totals[estimateKey]
  
  // Update construction cost in expenses
  return {
    ...expenses,
    constructionCost: estimatedCost,
    constructionArea: buildEstimate.metadata.area_m2,
    constructionCostPerSqm: buildEstimate.metadata.base_cost_per_sqm,
    buildEstimate: buildEstimate
  }
}

export async function fetchBuildCostEstimate(
  area_m2: number,
  scope: string[],
  region: string = 'CENTER',
  quality: string = 'standard'
): Promise<BuildCostEstimate> {
  const response = await fetch('/api/cost/estimate/build', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      area_m2,
      scope,
      region,
      quality
    })
  })
  
  if (!response.ok) {
    throw new Error('Failed to fetch build cost estimate')
  }
  
  return response.json()
}

export async function fetchCostOptions(): Promise<CostEstimateOptions> {
  const response = await fetch('/api/cost/options')
  
  if (!response.ok) {
    throw new Error('Failed to fetch cost options')
  }
  
  return response.json()
}
