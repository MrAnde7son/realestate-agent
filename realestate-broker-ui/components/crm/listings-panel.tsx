'use client'

import React, { useState, useEffect, useCallback, useMemo } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/Badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ExternalLink, RefreshCw, Loader2, ArrowDown, ArrowUp, ArrowUpDown, Phone, Play } from 'lucide-react'
import { api } from '@/lib/api-client'
import TableToolbar, { AdditionalFilterValue } from '@/components/TableToolbar'
import { useDedupedEffect } from '@/hooks/use-deduped-effect'

const PAGE_SIZE_OPTIONS = [10, 20, 50, 100]

const SOURCE_DISPLAY: Record<string, string> = {
  yad2: 'יד2',
  madlan: 'מדלן',
  homeless: 'Homeless',
  winwin: 'WinWin',
}

const SOURCE_COLOR: Record<string, string> = {
  yad2: 'bg-blue-100 text-blue-800',
  madlan: 'bg-green-100 text-green-800',
  homeless: 'bg-purple-100 text-purple-800',
  winwin: 'bg-orange-100 text-orange-800',
}

interface Listing {
  id: string
  title: string
  price?: number | null
  address?: string | null
  rooms?: number | null
  rooms_display?: string | null
  size?: number | null
  property_type?: string | null
  source?: string | null
  url?: string | null
  date_posted?: string | null
  images?: string[]
  description?: string | null
  floor?: string | number | null
  features?: string[]
  listing_type?: string | null
  listingType?: string | null
  contact_name?: string | null
  contactName?: string | null
  contact_phone?: string | null
  contactPhone?: string | null
  contact_info?: {
    name?: string | null
    phone?: string | null
    brokerPhone?: string | null
    email?: string | null
  } | null
  contactInfo?: {
    name?: string | null
    phone?: string | null
    brokerPhone?: string | null
    email?: string | null
  } | null
  recent_deal?: boolean | null
  recentDeal?: boolean | null
  photos?: string[]
  video_url?: string | null
  videoUrl?: string | null
}

interface ListingsFiltersMeta {
  source: string[]
  property_type: string[]
  rooms: string[]
  price: {
    min: number | null
    max: number | null
  }
  listing_type?: string[]
}

interface ListingsState {
  items: Listing[]
  total: number
  totalAll: number
  limit: number
  offset: number
  ordering: string
  filters: ListingsFiltersMeta
}

const DEFAULT_LISTINGS_STATE: ListingsState = {
  items: [],
  total: 0,
  totalAll: 0,
  limit: PAGE_SIZE_OPTIONS[0],
  offset: 0,
  ordering: '-date_posted',
  filters: {
    source: [],
    property_type: [],
    listing_type: [],
    rooms: [],
    price: { min: null, max: null },
  },
}

const formatNumber = (value: number) => new Intl.NumberFormat('he-IL').format(value)

const formatPrice = (price?: number | null) => {
  if (price === null || price === undefined) {
    return 'לא צוין'
  }
  return `${formatNumber(price)} ₪`
}

const formatRooms = (rooms?: number | null, roomsDisplay?: string | null) => {
  if (roomsDisplay) {
    return `${roomsDisplay} חדרים`
  }
  if (rooms === null || rooms === undefined) {
    return 'לא צוין'
  }
  if (Number.isInteger(rooms)) {
    return `${rooms} חדרים`
  }
  return `${parseFloat(rooms.toFixed(2)).toString()} חדרים`
}

const formatSize = (size?: number | null) => {
  if (size === null || size === undefined || Number.isNaN(size)) {
    return '—'
  }
  return `${Math.round(size)} מ״ר`
}

const formatListingType = (value?: string | null) => {
  if (!value) return 'לא צוין'
  const normalized = value.toLowerCase()
  if (normalized === 'rent') return 'השכרה'
  if (normalized === 'sale') return 'מכירה'
  if (normalized === 'commercial') return 'מסחרי'
  return value
}

const normalizeListingResponse = (listing: any): Listing => {
  if (!listing || typeof listing !== 'object') {
    return listing
  }

  const rawContact = listing.contactInfo ?? listing.contact_info
  const baseContact: Record<string, any> =
    rawContact && typeof rawContact === 'object' ? { ...rawContact } : {}

  const contactName =
    listing.contactName ?? listing.contact_name ?? baseContact.name ?? null
  const contactPhone =
    listing.contactPhone ??
    listing.contact_phone ??
    baseContact.phone ??
    baseContact.brokerPhone ??
    null

  if (contactName != null) {
    baseContact.name = contactName
  }
  if (contactPhone != null) {
    baseContact.phone = contactPhone
  }

  const photos = Array.from(
    new Set([
      ...(Array.isArray(listing.photos) ? listing.photos : []),
      ...(Array.isArray(listing.images) ? listing.images : []),
    ])
  )

  const videoUrl = listing.videoUrl ?? listing.video_url ?? listing.video ?? null

  let recentDeal: boolean | null = null
  if (typeof listing.recentDeal === 'boolean') {
    recentDeal = listing.recentDeal
  } else if (typeof listing.recent_deal === 'boolean') {
    recentDeal = listing.recent_deal
  }

  return {
    ...listing,
    listingType: listing.listingType ?? listing.listing_type ?? null,
    listing_type: listing.listingType ?? listing.listing_type ?? null,
    contactName,
    contact_name: contactName,
    contactPhone,
    contact_phone: contactPhone,
    contactInfo: Object.keys(baseContact).length > 0 ? baseContact : null,
    contact_info: Object.keys(baseContact).length > 0 ? baseContact : null,
    photos,
    videoUrl,
    video_url: videoUrl,
    recentDeal,
    recent_deal: recentDeal,
  }
}

const formatDate = (value?: string | null) => {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return date.toLocaleDateString('he-IL')
}

const getSourceDisplay = (source?: string | null) => {
  if (!source) return 'לא ידוע'
  return SOURCE_DISPLAY[source.toLowerCase()] || source
}

const getSourceColor = (source?: string | null) => {
  if (!source) return 'bg-gray-100 text-gray-800'
  return SOURCE_COLOR[source.toLowerCase()] || 'bg-gray-100 text-gray-800'
}

interface ListingsPanelProps {
  assetId: number
  assetAddress: string
}

export function ListingsPanel({ assetId }: ListingsPanelProps) {
  const [listingsState, setListingsState] = useState<ListingsState>(DEFAULT_LISTINGS_STATE)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [sourceFilter, setSourceFilter] = useState('all')
  const [propertyTypeFilter, setPropertyTypeFilter] = useState('all')
  const [listingTypeFilter, setListingTypeFilter] = useState('all')
  const [roomsFilter, setRoomsFilter] = useState('all')
  const [priceMin, setPriceMin] = useState<number | undefined>(undefined)
  const [priceMax, setPriceMax] = useState<number | undefined>(undefined)
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: PAGE_SIZE_OPTIONS[0] })
  const [ordering, setOrdering] = useState('-date_posted')

  const resetPageIndex = useCallback(() => {
    setPagination((prev) => (prev.pageIndex === 0 ? prev : { ...prev, pageIndex: 0 }))
  }, [])

  const handleSearchChange = useCallback((value: string) => {
    setSearchTerm(value)
    resetPageIndex()
  }, [resetPageIndex])

  const handlePriceMinChange = useCallback((value?: number) => {
    setPriceMin(value)
    resetPageIndex()
  }, [resetPageIndex])

  const handlePriceMaxChange = useCallback((value?: number) => {
    setPriceMax(value)
    resetPageIndex()
  }, [resetPageIndex])

  const handleAdditionalFilterChange = useCallback((key: string, value: AdditionalFilterValue) => {
    if (typeof value !== 'string') {
      return
    }
    switch (key) {
      case 'rooms':
        setRoomsFilter(value)
        break
      case 'propertyType':
        setPropertyTypeFilter(value)
        break
      case 'source':
        setSourceFilter(value)
        break
      case 'listingType':
        setListingTypeFilter(value)
        break
      default:
        break
    }
    resetPageIndex()
  }, [resetPageIndex])

  const toggleOrdering = useCallback((field: string) => {
    setOrdering((prev) => {
      if (prev === field) return `-${field}`
      if (prev === `-${field}`) return field
      return `-${field}`
    })
    resetPageIndex()
  }, [resetPageIndex])

  const getSortIcon = useCallback((field: string) => {
    if (ordering === field) {
      return <ArrowUp className="h-3 w-3 text-muted-foreground" />
    }
    if (ordering === `-${field}`) {
      return <ArrowDown className="h-3 w-3 text-muted-foreground" />
    }
    return <ArrowUpDown className="h-3 w-3 text-muted-foreground" />
  }, [ordering])

  const fetchListings = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const params = new URLSearchParams()
      params.set('limit', String(pagination.pageSize))
      params.set('offset', String(pagination.pageIndex * pagination.pageSize))
      if (searchTerm.trim()) {
        params.set('search', searchTerm.trim())
      }
      if (sourceFilter !== 'all') {
        params.set('source', sourceFilter)
      }
      if (propertyTypeFilter !== 'all') {
        params.set('property_type', propertyTypeFilter)
      }
      if (listingTypeFilter !== 'all') {
        params.set('listing_type', listingTypeFilter)
      }
      if (roomsFilter !== 'all') {
        params.set('rooms', roomsFilter)
      }
      if (priceMin !== undefined) {
        params.set('min_price', String(priceMin))
      }
      if (priceMax !== undefined) {
        params.set('max_price', String(priceMax))
      }
      if (ordering) {
        params.set('ordering', ordering)
      }

      const response = await api.get(`/api/assets/${assetId}/listings?${params.toString()}`)

      if (!response.ok) {
        throw new Error(response.error || 'Failed to fetch listings')
      }

      const data = response.data ?? {}
      const items: Listing[] = Array.isArray(data?.results)
        ? data.results.map(normalizeListingResponse)
        : []
      const serverLimit = typeof data?.limit === 'number' && data.limit > 0 ? data.limit : pagination.pageSize
      const serverOffset = typeof data?.offset === 'number' && data.offset >= 0 ? data.offset : pagination.pageIndex * pagination.pageSize
      const sanitizedOrdering = typeof data?.ordering === 'string' && data.ordering ? data.ordering : ordering

      const nextState: ListingsState = {
        items,
        total: typeof data?.count === 'number' ? data.count : items.length,
        totalAll: typeof data?.total_all === 'number'
          ? data.total_all
          : (typeof data?.total === 'number' ? data.total : items.length),
        limit: serverLimit,
        offset: serverOffset,
        ordering: sanitizedOrdering,
        filters: {
          source: Array.isArray(data?.filters?.source) ? data.filters.source : [],
          property_type: Array.isArray(data?.filters?.property_type) ? data.filters.property_type : [],
          listing_type: Array.isArray(data?.filters?.listing_type) ? data.filters.listing_type : [],
          rooms: Array.isArray(data?.filters?.rooms) ? data.filters.rooms : [],
          price: {
            min: typeof data?.filters?.price?.min === 'number' ? data.filters.price.min : null,
            max: typeof data?.filters?.price?.max === 'number' ? data.filters.price.max : null,
          },
        },
      }

      setListingsState(nextState)

      if (sanitizedOrdering !== ordering) {
        setOrdering(sanitizedOrdering)
      }

      if (serverLimit !== pagination.pageSize || serverOffset !== pagination.pageIndex * pagination.pageSize) {
        const nextPageIndex = serverLimit > 0 ? Math.floor(serverOffset / serverLimit) : 0
        setPagination((prev) => {
          if (prev.pageSize === serverLimit && prev.pageIndex === nextPageIndex) {
            return prev
          }
          return {
            pageIndex: Math.max(0, nextPageIndex),
            pageSize: serverLimit,
          }
        })
      }
    } catch (err) {
      console.error('Error fetching listings:', err)
      setError('שגיאה בטעינת המודעות')
      setListingsState(DEFAULT_LISTINGS_STATE)
    } finally {
      setLoading(false)
    }
  }, [
    assetId,
    pagination.pageIndex,
    pagination.pageSize,
    searchTerm,
    sourceFilter,
    propertyTypeFilter,
    roomsFilter,
    priceMin,
    priceMax,
    ordering,
    listingTypeFilter,
  ])

  useDedupedEffect(() => {
    fetchListings()
  }, [fetchListings])

  const roomOptions = useMemo(() => {
    const serverRooms = Array.isArray(listingsState.filters.rooms)
      ? listingsState.filters.rooms.filter(Boolean)
      : []

    if (serverRooms.length > 0) {
      return serverRooms.map((room) => ({
        value: room,
        label: room.includes('חדר') ? room : `${room} חדרים`,
      }))
    }

    const derived = new Map<string, { value: string; label: string }>()

    listingsState.items.forEach((listing) => {
      if (listing.rooms === null || listing.rooms === undefined || Number.isNaN(listing.rooms)) {
        return
      }
      const value = String(listing.rooms)
      if (derived.has(value)) {
        return
      }
      const label = formatRooms(listing.rooms, listing.rooms_display)
      derived.set(value, { value, label })
    })

    return Array.from(derived.values())
  }, [listingsState.filters.rooms, listingsState.items])

  const listingTypeOptions = useMemo(() => {
    if (!Array.isArray(listingsState.filters.listing_type)) {
      return [] as Array<{ value: string; label: string }>
    }
    return listingsState.filters.listing_type.map(type => ({
      value: type,
      label: formatListingType(type),
    }))
  }, [listingsState.filters.listing_type])

  const sourceOptions = useMemo(() => {
    const serverSources = Array.isArray(listingsState.filters.source)
      ? listingsState.filters.source.filter(Boolean)
      : []

    if (serverSources.length > 0) {
      return serverSources.map((source) => ({
        value: source.toLowerCase(),
        label: getSourceDisplay(source),
      }))
    }

    const derived = new Map<string, { value: string; label: string }>()

    listingsState.items.forEach((listing) => {
      if (!listing.source) {
        return
      }
      const value = listing.source.toLowerCase()
      if (derived.has(value)) {
        return
      }
      const label = getSourceDisplay(listing.source)
      derived.set(value, { value, label })
    })

    return Array.from(derived.values())
  }, [listingsState.filters.source, listingsState.items])

  useEffect(() => {
    if (
      sourceFilter !== 'all' &&
      sourceOptions.length > 0 &&
      !sourceOptions.some((option) => option.value === sourceFilter)
    ) {
      setSourceFilter('all')
    }
    if (
      propertyTypeFilter !== 'all' &&
      listingsState.filters.property_type.length > 0 &&
      !listingsState.filters.property_type.includes(propertyTypeFilter)
    ) {
      setPropertyTypeFilter('all')
    }
    if (
      listingTypeFilter !== 'all' &&
      Array.isArray(listingsState.filters.listing_type) &&
      listingsState.filters.listing_type.length > 0 &&
      !listingsState.filters.listing_type.includes(listingTypeFilter)
    ) {
      setListingTypeFilter('all')
    }
    if (
      roomsFilter !== 'all' &&
      roomOptions.length > 0 &&
      !roomOptions.some((option) => option.value === roomsFilter)
    ) {
      setRoomsFilter('all')
    }
  }, [
    listingsState.filters.property_type,
    listingsState.filters.listing_type,
    roomOptions,
    sourceOptions,
    sourceFilter,
    propertyTypeFilter,
    listingTypeFilter,
    roomsFilter,
  ])

  const additionalFilters = useMemo(() => {
    const filters: Array<{
      key: string
      label: string
      value: string
      options: Array<{ value: string; label: string }>
    }> = []

    if (roomOptions.length > 0) {
      filters.push({
        key: 'rooms',
        label: 'חדרים',
        value: roomsFilter,
        options: [
          { value: 'all', label: 'כל החדרים' },
          ...roomOptions,
        ],
      })
    }

    if (listingsState.filters.property_type.length > 0) {
      filters.push({
        key: 'propertyType',
        label: 'סוג נכס',
        value: propertyTypeFilter,
        options: [
          { value: 'all', label: 'כל הסוגים' },
          ...listingsState.filters.property_type.map((type) => ({
            value: type,
            label: type,
          })),
        ],
      })
    }

    if (listingTypeOptions.length > 0) {
      filters.push({
        key: 'listingType',
        label: 'סוג עסקה',
        value: listingTypeFilter,
        options: [
          { value: 'all', label: 'כל העסקאות' },
          ...listingTypeOptions,
        ],
      })
    }

    if (sourceOptions.length > 0) {
      filters.push({
        key: 'source',
        label: 'מקור',
        value: sourceFilter,
        options: [
          { value: 'all', label: 'כל המקורות' },
          ...sourceOptions,
        ],
      })
    }

    return filters
  }, [
    listingsState.filters.property_type,
    sourceOptions,
    listingTypeOptions,
    roomOptions,
    roomsFilter,
    propertyTypeFilter,
    listingTypeFilter,
    sourceFilter,
  ])

  const totalPages = Math.max(1, Math.ceil(listingsState.total / pagination.pageSize))
  const canGoPrev = pagination.pageIndex > 0
  const canGoNext = (pagination.pageIndex + 1) * pagination.pageSize < listingsState.total

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div className="text-right">
              <CardTitle>מודעות</CardTitle>
              <p className="text-sm text-muted-foreground">
                מודעות נדלן מהמקורות השונים
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchListings}
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin ms-2" />
                  טוען...
                </>
              ) : (
                <>
                  <RefreshCw className="h-4 w-4 ms-2" />
                  רענן
                </>
              )}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="surface-panel overflow-x-auto">
            <TableToolbar
              searchValue={searchTerm}
              onSearchChange={handleSearchChange}
              searchPlaceholder="חיפוש במודעות..."
              filters={{
                priceMin: {
                  value: priceMin,
                  onChange: handlePriceMinChange,
                  label: 'מחיר מינימלי',
                  placeholder: '₪',
                  analyticsKey: 'price_min',
                },
                priceMax: {
                  value: priceMax,
                  onChange: handlePriceMaxChange,
                  label: 'מחיר מקסימלי',
                  placeholder: '₪',
                  analyticsKey: 'price_max',
                },
              }}
              additionalFilters={additionalFilters}
              onAdditionalFilterChange={handleAdditionalFilterChange}
              columns={[]}
              selectedCount={0}
              totalCount={listingsState.total}
              onExportSelected={() => {}}
              onExportAll={() => {}}
              viewMode="table"
              onViewModeChange={() => {}}
              onRefresh={fetchListings}
              loading={loading}
            />

            <div className="px-4 py-2 border-b border-border bg-muted/30" dir="rtl">
              <div className="flex justify-between items-center text-sm text-muted-foreground">
                <span>נמצאו {formatNumber(listingsState.total)} מודעות</span>
                {listingsState.totalAll !== listingsState.total && (
                  <span>מתוך {formatNumber(listingsState.totalAll)} מודעות</span>
                )}
              </div>
            </div>

            {loading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin" />
              </div>
            ) : error ? (
              <div className="text-center py-8 text-red-500 space-y-3">
                <p>{error}</p>
                <Button onClick={fetchListings} variant="outline">
                  נסה שוב
                </Button>
              </div>
            ) : listingsState.items.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <p>לא נמצאו מודעות מתאימות</p>
              </div>
            ) : (
              <div className="relative rtl">
                <Table className="rtl">
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-start rtl:text-start w-[200px] min-w-[200px]">כותרת</TableHead>
                      <TableHead className="text-start rtl:text-start w-[120px] min-w-[120px]">סוג עסקה</TableHead>
                      <TableHead className="text-start rtl:text-start w-[150px] min-w-[150px]">איש קשר</TableHead>
                      <TableHead className="text-start rtl:text-start w-[120px] min-w-[120px]">נמכר לאחרונה</TableHead>
                      <TableHead className="text-start rtl:text-start w-[80px] min-w-[80px]">וידאו</TableHead>
                      <TableHead className="text-start rtl:text-start w-[100px] min-w-[100px]">
                        <button
                          type="button"
                          onClick={() => toggleOrdering('price')}
                          className="flex items-center justify-start gap-1 w-full text-sm font-medium"
                        >
                          מחיר
                          {getSortIcon('price')}
                        </button>
                      </TableHead>
                      <TableHead className="text-start rtl:text-start w-[90px] min-w-[90px]">
                        <button
                          type="button"
                          onClick={() => toggleOrdering('rooms')}
                          className="flex items-center justify-start gap-1 w-full text-sm font-medium"
                        >
                          חדרים
                          {getSortIcon('rooms')}
                        </button>
                      </TableHead>
                      <TableHead className="text-start rtl:text-start w-[90px] min-w-[90px]">
                        <button
                          type="button"
                          onClick={() => toggleOrdering('size')}
                          className="flex items-center justify-start gap-1 w-full text-sm font-medium"
                        >
                          גודל
                          {getSortIcon('size')}
                        </button>
                      </TableHead>
                      <TableHead className="text-start rtl:text-start w-[90px] min-w-[90px]">
                        <button
                          type="button"
                          onClick={() => toggleOrdering('source')}
                          className="flex items-center justify-start gap-1 w-full text-sm font-medium"
                        >
                          מקור
                          {getSortIcon('source')}
                        </button>
                      </TableHead>
                      <TableHead className="text-start rtl:text-start w-[100px] min-w-[100px]">
                        <button
                          type="button"
                          onClick={() => toggleOrdering('date_posted')}
                          className="flex items-center justify-start gap-1 w-full text-sm font-medium"
                        >
                          תאריך
                          {getSortIcon('date_posted')}
                        </button>
                      </TableHead>
                      <TableHead className="text-start rtl:text-start w-[80px] min-w-[80px]">פעולות</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {listingsState.items.map((listing, index) => (
                      <TableRow key={listing.id || `${listing.source || 'listing'}-${index}`} className="hover:bg-muted/50">
                        <TableCell className="text-start rtl:text-start align-top whitespace-normal">
                          <div className="space-y-1 pr-2">
                            <p className="font-medium break-words">{listing.title || '—'}</p>
                            {listing.address && (
                              <p className="text-sm text-muted-foreground break-words">{listing.address}</p>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="text-start rtl:text-start align-top">
                          <Badge className="whitespace-nowrap">{formatListingType(listing.listingType ?? listing.listing_type)}</Badge>
                        </TableCell>
                        <TableCell className="text-start rtl:text-start align-top">
                          {(() => {
                            const name = listing.contactName ?? listing.contact_name ?? listing.contactInfo?.name ?? listing.contact_info?.name
                            const phone =
                              listing.contactPhone ??
                              listing.contact_phone ??
                              listing.contactInfo?.phone ??
                              listing.contactInfo?.brokerPhone ??
                              listing.contact_info?.phone ??
                              listing.contact_info?.brokerPhone
                            if (!name && !phone) {
                              return <span>—</span>
                            }
                            const sanitizedPhone = phone ? phone.replace(/[^+\d]/g, '') : ''
                            return (
                              <div className="flex flex-col gap-1 text-xs pr-2">
                                {name && <span className="font-medium text-foreground break-words">{name}</span>}
                                {phone && (
                                  <a
                                    href={sanitizedPhone ? `tel:${sanitizedPhone}` : undefined}
                                    className="inline-flex items-center gap-1 text-primary hover:underline whitespace-nowrap"
                                    onClick={event => event.stopPropagation()}
                                  >
                                    <Phone className="h-3 w-3 flex-shrink-0" />
                                    <span dir="ltr">{phone}</span>
                                  </a>
                                )}
                              </div>
                            )
                          })()}
                        </TableCell>
                        <TableCell className="text-start rtl:text-start align-top">
                          {typeof (listing.recentDeal ?? listing.recent_deal) === 'boolean' ? (
                            <Badge variant={(listing.recentDeal ?? listing.recent_deal) ? 'success' : 'neutral'} className="whitespace-nowrap">
                              {(listing.recentDeal ?? listing.recent_deal) ? 'כן' : 'לא'}
                            </Badge>
                          ) : (
                            <Badge variant="neutral">—</Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-start rtl:text-start align-top">
                          {(() => {
                            const videoUrl = listing.videoUrl ?? listing.video_url ?? listing.url
                            if (!videoUrl) {
                              return <span>—</span>
                            }
                          return (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={event => {
                                event.stopPropagation()
                                window.open(videoUrl, '_blank', 'noopener')
                              }}
                              className="me-0"
                              aria-label="פתח וידאו"
                            >
                              <Play className="h-4 w-4" />
                            </Button>
                          )
                        })()}
                        </TableCell>
                        <TableCell className="text-start rtl:text-start align-top">
                          <span dir="ltr" className="block text-end font-medium">
                            {formatPrice(listing.price)}
                          </span>
                        </TableCell>
                        <TableCell className="text-start rtl:text-start align-top">
                          {formatRooms(listing.rooms, listing.rooms_display)}
                        </TableCell>
                        <TableCell className="text-start rtl:text-start align-top">
                          <span dir="ltr" className="block text-end">
                            {formatSize(listing.size)}
                          </span>
                        </TableCell>
                        <TableCell className="text-start rtl:text-start align-top">
                          <Badge className={getSourceColor(listing.source)}>
                            {getSourceDisplay(listing.source)}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-start rtl:text-start align-top">
                          <span dir="ltr" className="block text-end">
                            {formatDate(listing.date_posted)}
                          </span>
                        </TableCell>
                        <TableCell className="text-start rtl:text-start align-top">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => listing.url && window.open(listing.url, '_blank')}
                            className="me-0 ms-2"
                            disabled={!listing.url}
                          >
                            <ExternalLink className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 px-4 py-3 border-t border-border">
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPagination((prev) => ({ ...prev, pageIndex: Math.max(0, prev.pageIndex - 1) }))}
                disabled={!canGoPrev}
              >
                הקודם
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPagination((prev) => ({ ...prev, pageIndex: prev.pageIndex + 1 }))}
                disabled={!canGoNext}
              >
                הבא
              </Button>
            </div>

            <div className="text-sm text-muted-foreground">
              עמוד {pagination.pageIndex + 1} מתוך {totalPages}
            </div>

            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">שורות בעמוד</span>
              <Select
                value={String(pagination.pageSize)}
                onValueChange={(value) =>
                  setPagination({ pageIndex: 0, pageSize: Number(value) })
                }
              >
                <SelectTrigger className="w-[90px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PAGE_SIZE_OPTIONS.map((size) => (
                    <SelectItem key={size} value={String(size)}>
                      {size}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
