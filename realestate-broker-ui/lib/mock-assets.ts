import type { Asset } from '@/lib/normalizers/asset'

export const mockAssets: Asset[] = [
  {
    id: 1,
    address: 'הרצל 1',
    city: 'תל אביב',
    rooms: 3,
    bathrooms: 1,
    area: 75,
    price: 2000000,
    pricePerSqm: 26667,
    assetStatus: 'done'
  },
  {
    id: 2,
    address: 'דרך השלום 10',
    city: 'חיפה',
    rooms: 4,
    bathrooms: 2,
    area: 90,
    price: 1500000,
    pricePerSqm: 16667,
    assetStatus: 'enriching'
  },
  {
    id: 3,
    address: 'העצמאות 5',
    city: 'ירושלים',
    rooms: 2,
    bathrooms: 1,
    area: 60,
    price: 1200000,
    pricePerSqm: 20000,
    assetStatus: 'pending'
  }
]

export const getMockAsset = (id: number) =>
  mockAssets.find(asset => asset.id === id)
