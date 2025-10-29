import type { Asset } from '@/lib/normalizers/asset'

const numberFormatter = new Intl.NumberFormat('he-IL')
const compactNumberFormatter = new Intl.NumberFormat('he-IL', {
  notation: 'compact',
  maximumFractionDigits: 1,
})

export interface MarkerDisplayData {
  id: number | string
  shortAddress: string
  fullAddress: string
  priceLabel: string | null
  areaLabel: string | null
  roomsLabel: string | null
  propertyType: string | null
  pricePerSqmLabel: string | null
  features: string[]
  photoUrl: string | null
  cityLine: string | null
  sourceLabel: string | null
}

const WHITESPACE_REGEX = /\s+/g
const DENSE_ASSET_THRESHOLD = 12
const DETAIL_ZOOM_THRESHOLD = 13.5

const clean = (value: string | null | undefined): string | null => {
  if (!value) return null
  const trimmed = value.replace(WHITESPACE_REGEX, ' ').trim()
  return trimmed.length ? trimmed : null
}

const isNonEmptyString = (value: string | null | undefined): value is string => {
  const cleaned = clean(value)
  return Boolean(cleaned)
}

export const truncateMiddle = (value: string, maxLength: number): string => {
  if (value.length <= maxLength) return value
  if (maxLength <= 3) return value.slice(0, maxLength)
  const keep = maxLength - 1
  return `${value.slice(0, keep)}…`
}

export const formatPriceLabel = (value: number | null | undefined): string | null => {
  if (value == null || Number.isNaN(value)) return null
  if (value >= 1_000_000) {
    return `${compactNumberFormatter.format(value)} ₪`
  }
  return `${numberFormatter.format(value)} ₪`
}

export const formatAreaLabel = (value: number | null | undefined): string | null => {
  if (value == null || Number.isNaN(value)) return null
  return `${numberFormatter.format(Math.round(value))} מ״ר`
}

export const formatRoomsLabel = (value: number | null | undefined): string | null => {
  if (value == null || Number.isNaN(value)) return null
  const rounded = Math.round(value * 2) / 2
  return `${rounded} חדרים`
}

export const formatPricePerSqmLabel = (
  price: number | null | undefined,
  area: number | null | undefined,
  explicit?: number | null | undefined
): string | null => {
  if (explicit != null && !Number.isNaN(explicit)) {
    return `${numberFormatter.format(Math.round(explicit))} ₪ למ״ר`
  }
  if (price == null || area == null || !area || Number.isNaN(price) || Number.isNaN(area)) return null
  const pricePerSqm = Math.round(price / area)
  if (!Number.isFinite(pricePerSqm)) return null
  return `${numberFormatter.format(pricePerSqm)} ₪ למ״ר`
}

const pickPhoto = (asset: Asset): string | null => {
  const sources = [asset.photos, asset.images, asset.primaryListing?.photos]
  for (const collection of sources) {
    if (!collection || !collection.length) continue
    const first = collection.find(src => clean(src))
    if (first) return clean(first)!
  }
  return null
}

const buildAddress = (asset: Asset): { shortAddress: string; fullAddress: string; cityLine: string | null } => {
  const streetParts = [clean(asset.street), asset.number != null ? String(asset.number) : null].filter(isNonEmptyString)
  const streetLine = clean(streetParts.join(' '))
  const apartmentLine = clean(asset.apartment ? `דירה ${asset.apartment}` : null)
  const primaryCandidates = [
    clean(asset.address),
    clean(asset.normalizedAddress),
    clean(asset.primaryListing?.address ?? null),
    streetLine,
  ]
  const baseCandidate = primaryCandidates.find(isNonEmptyString)
  const baseAddress = baseCandidate ?? `נכס ${asset.id}`

  const cityCandidates = [clean(asset.city), clean(asset.primaryListing?.address?.split(',').pop())]
  const cityCandidate = cityCandidates.find(val => isNonEmptyString(val) && !baseAddress.includes(val))
  const city = cityCandidate ?? clean(asset.city)

  const addressParts = [baseAddress]
  if (apartmentLine && !baseAddress.includes(apartmentLine)) addressParts.push(apartmentLine)
  if (city && !baseAddress.includes(city)) addressParts.push(city)

  const fullAddress = addressParts.join(', ')
  const shortAddress = truncateMiddle(baseAddress, 30)

  return { shortAddress, fullAddress, cityLine: city ?? null }
}

const collectFeatures = (asset: Asset): string[] => {
  const collections = [asset.features, asset.primaryListing?.features]
  for (const collection of collections) {
    if (!collection || !collection.length) continue
    const cleaned = collection.map(item => clean(item)).filter(isNonEmptyString)
    if (cleaned.length) {
      return cleaned.slice(0, 3)
    }
  }
  return []
}

const pickPrice = (asset: Asset): number | null => {
  const candidates = [asset.price, asset.primaryListing?.price, asset.rentPrice, asset.primaryListing?.rentPrice]
  const candidate = candidates.find(value => value != null && !Number.isNaN(value))
  return candidate != null ? Number(candidate) : null
}

const pickArea = (asset: Asset): number | null => {
  const candidates = [asset.area, asset.totalArea, asset.subparcelArea, asset.primaryListing?.size]
  const candidate = candidates.find(value => value != null && !Number.isNaN(value))
  return candidate != null ? Number(candidate) : null
}

const pickRooms = (asset: Asset): number | null => {
  const candidates = [asset.rooms, asset.bedrooms, asset.primaryListing?.rooms]
  const candidate = candidates.find(value => value != null && !Number.isNaN(value))
  return candidate != null ? Number(candidate) : null
}

const pickPropertyType = (asset: Asset): string | null => {
  const candidates = [asset.type, asset.buildingType, asset.primaryListing?.propertyType, asset.listingType]
  const candidate = candidates.find(value => isNonEmptyString(value))
  return candidate ? clean(candidate)! : null
}

const pickPricePerSqm = (asset: Asset): number | null => {
  const candidates = [asset.pricePerSqm, asset.pricePerSqmDisplay]
  const candidate = candidates.find(value => value != null && !Number.isNaN(value))
  return candidate != null ? Number(candidate) : null
}

const pickSource = (asset: Asset): string | null => {
  const candidates = [asset.primaryListing?.source, asset.primarySource]
  if (asset.sources && asset.sources.length) {
    candidates.push(asset.sources[0] ?? null)
  }
  const candidate = candidates.find(value => isNonEmptyString(value))
  return candidate ? clean(candidate)! : null
}

export const buildMarkerDisplayData = (asset: Asset): MarkerDisplayData => {
  const { shortAddress, fullAddress, cityLine } = buildAddress(asset)
  const price = pickPrice(asset)
  const area = pickArea(asset)
  const rooms = pickRooms(asset)
  const propertyType = pickPropertyType(asset)
  const photoUrl = pickPhoto(asset)
  const features = collectFeatures(asset)
  const pricePerSqmExplicit = pickPricePerSqm(asset)
  const sourceLabel = pickSource(asset)

  return {
    id: asset.id,
    shortAddress,
    fullAddress,
    priceLabel: formatPriceLabel(price),
    areaLabel: formatAreaLabel(area),
    roomsLabel: formatRoomsLabel(rooms),
    propertyType,
    pricePerSqmLabel: formatPricePerSqmLabel(price, area, pricePerSqmExplicit),
    features,
    photoUrl,
    cityLine,
    sourceLabel,
  }
}

export const shouldDisplayMarkerLabel = ({
  totalAssets,
  zoom,
  preferTouchDevice = false,
}: {
  totalAssets: number
  zoom?: number | null
  preferTouchDevice?: boolean
}): boolean => {
  if (totalAssets <= 0) return false
  if (preferTouchDevice) return true
  if (totalAssets <= DENSE_ASSET_THRESHOLD) return true
  const effectiveZoom = zoom ?? 0
  if (effectiveZoom >= DETAIL_ZOOM_THRESHOLD) return true
  return false
}

export type { Asset }
