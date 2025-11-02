import { render, screen } from '@testing-library/react'

import AssetCard from '@/components/AssetCard'

const baseAsset = {
  id: 1,
  address: 'רחוב הבדיקה 1',
  assetStatus: 'done',
  price: 1200000,
  rooms: 4,
  bathrooms: 2,
  area: 95,
  pricePerSqm: 12631,
  images: [],
} as const

describe('AssetCard accessibility affordances', () => {
  it('provides accessible names for icon-only actions', () => {
    render(<AssetCard asset={baseAsset} />)

    expect(screen.getByRole('button', { name: 'צפה בפרטים' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'ייצוא פרטי נכס' })).toBeInTheDocument()
  })
})
