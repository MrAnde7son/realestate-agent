'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/Badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Search, Filter, ExternalLink, RefreshCw, Loader2 } from 'lucide-react'
import { api } from '@/lib/api-client'
import TableToolbar from '@/components/TableToolbar'
import { useAnalytics } from '@/hooks/useAnalytics'

interface Listing {
  id: string
  title: string
  price: number
  address: string
  rooms: number
  size: number
  property_type: string
  source: string
  url: string
  date_posted: string
  images: string[]
  description: string
}

interface ListingsPanelProps {
  assetId: number
  assetAddress: string
}

export function ListingsPanel({ assetId, assetAddress }: ListingsPanelProps) {
  const { trackFeatureUsage } = useAnalytics()
  const [listings, setListings] = useState<Listing[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [priceRange, setPriceRange] = useState({ min: '', max: '' })
  const [roomsFilter, setRoomsFilter] = useState('all')
  const [propertyTypeFilter, setPropertyTypeFilter] = useState('all')
  const [sourceFilter, setSourceFilter] = useState('all')

  // Fetch listings from Yad2 and other sources
  const fetchListings = useCallback(async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await api.get(`/api/assets/${assetId}/listings/`)
      
      if (response.ok) {
        setListings(response.data.listings || [])
      } else {
        throw new Error(response.data?.error || 'Failed to fetch listings')
      }
    } catch (err) {
      console.error('Error fetching listings:', err)
      setError('שגיאה בטעינת המודעות')
      
      // Fallback to mock data if API fails
      const mockListings: Listing[] = [
        {
          id: '1',
          title: 'דירה 4 חדרים בתל אביב',
          price: 2500000,
          address: 'רחוב הרצל 15, תל אביב',
          rooms: 4,
          size: 95,
          property_type: 'דירה',
          source: 'yad2',
          url: 'https://www.yad2.co.il/item/123456',
          date_posted: '2024-01-15',
          images: [],
          description: 'דירה מרווחת עם מרפסת גדולה'
        },
        {
          id: '2',
          title: 'דירה 3 חדרים בתל אביב',
          price: 1800000,
          address: 'רחוב דיזנגוף 25, תל אביב',
          rooms: 3,
          size: 75,
          property_type: 'דירה',
          source: 'yad2',
          url: 'https://www.yad2.co.il/item/123457',
          date_posted: '2024-01-14',
          images: [],
          description: 'דירה מעוצבת במרכז העיר'
        },
        {
          id: '3',
          title: 'דירה 5 חדרים בתל אביב',
          price: 3200000,
          address: 'רחוב רוטשילד 10, תל אביב',
          rooms: 5,
          size: 120,
          property_type: 'דירה',
          source: 'madlan',
          url: 'https://www.madlan.co.il/item/789012',
          date_posted: '2024-01-13',
          images: [],
          description: 'דירה יוקרתית עם נוף לים'
        }
      ]
      
      setListings(mockListings)
    } finally {
      setLoading(false)
    }
  }, [assetId])

  useEffect(() => {
    fetchListings()
  }, [fetchListings])

  // Filter listings based on search and filter criteria
  const filteredListings = listings.filter(listing => {
    const matchesSearch = !searchTerm || 
      listing.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      listing.address.toLowerCase().includes(searchTerm.toLowerCase()) ||
      listing.description.toLowerCase().includes(searchTerm.toLowerCase())
    
    const matchesPrice = (!priceRange.min || listing.price >= parseInt(priceRange.min)) &&
      (!priceRange.max || listing.price <= parseInt(priceRange.max))
    
    const matchesRooms = !roomsFilter || roomsFilter === 'all' || listing.rooms.toString() === roomsFilter
    
    const matchesPropertyType = !propertyTypeFilter || propertyTypeFilter === 'all' || listing.property_type === propertyTypeFilter
    
    const matchesSource = !sourceFilter || sourceFilter === 'all' || listing.source === sourceFilter
    
    return matchesSearch && matchesPrice && matchesRooms && matchesPropertyType && matchesSource
  })

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('he-IL').format(price) + ' ₪'
  }

  const getSourceDisplay = (source: string) => {
    const sources: Record<string, string> = {
      'yad2': 'יד2',
      'madlan': 'מדלן',
      'homeless': 'Homeless'
    }
    return sources[source] || source
  }

  const getSourceColor = (source: string) => {
    const colors: Record<string, string> = {
      'yad2': 'bg-blue-100 text-blue-800',
      'madlan': 'bg-green-100 text-green-800',
      'homeless': 'bg-purple-100 text-purple-800'
    }
    return colors[source] || 'bg-gray-100 text-gray-800'
  }

  // Prepare additional filters for TableToolbar
  const additionalFilters = React.useMemo(() => {
    const filters = []
    
    if (listings.length > 0) {
      // Rooms filter
      const rooms = [...new Set(listings.map(listing => listing.rooms.toString()))]
      if (rooms.length > 1) {
        filters.push({
          key: 'rooms',
          label: 'חדרים',
          type: 'select',
          value: roomsFilter,
          options: [
            { value: 'all', label: 'כל החדרים' },
            ...rooms.map(room => ({
              value: room,
              label: `${room} חדרים`
            }))
          ]
        })
      }

      // Property type filter
      const propertyTypes = [...new Set(listings.map(listing => listing.property_type).filter(Boolean))]
      if (propertyTypes.length > 1) {
        filters.push({
          key: 'propertyType',
          label: 'סוג נכס',
          type: 'select',
          value: propertyTypeFilter,
          options: [
            { value: 'all', label: 'כל הסוגים' },
            ...propertyTypes.map(type => ({ value: type, label: type }))
          ]
        })
      }

      // Source filter
      const sources = [...new Set(listings.map(listing => listing.source))]
      if (sources.length > 1) {
        filters.push({
          key: 'source',
          label: 'מקור',
          type: 'select',
          value: sourceFilter,
          options: [
            { value: 'all', label: 'כל המקורות' },
            ...sources.map(source => ({
              value: source,
              label: getSourceDisplay(source)
            }))
          ]
        })
      }
    }

    return filters
  }, [listings, roomsFilter, propertyTypeFilter, sourceFilter])

  const handleAdditionalFilterChange = (key: string, value: string) => {
    trackFeatureUsage('filter', undefined, { filter_type: key, value })
    
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
      default:
        break
    }
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-right">מודעות</CardTitle>
          <p className="text-sm text-muted-foreground text-right">
            מודעות נדלן מהאתרים השונים
          </p>
        </CardHeader>
        <CardContent className="p-0">
          <div className="rounded-xl border border-border bg-card overflow-x-auto">
            {/* Integrated Toolbar */}
            <TableToolbar
              searchValue={searchTerm}
              onSearchChange={setSearchTerm}
              searchPlaceholder="חיפוש במודעות..."
              filters={{
                city: { value: 'all', onChange: () => {}, options: [] },
                type: { value: 'all', onChange: () => {}, options: [] },
                priceMin: { 
                  value: priceRange.min ? parseInt(priceRange.min) : undefined, 
                  onChange: (value) => setPriceRange(prev => ({ ...prev, min: value?.toString() || '' }))
                },
                priceMax: { 
                  value: priceRange.max ? parseInt(priceRange.max) : undefined, 
                  onChange: (value) => setPriceRange(prev => ({ ...prev, max: value?.toString() || '' }))
                }
              }}
              additionalFilters={additionalFilters}
              onAdditionalFilterChange={handleAdditionalFilterChange}
              columns={[]}
              selectedCount={0}
              totalCount={filteredListings.length}
              onExportSelected={() => {}}
              onExportAll={() => {}}
              viewMode="table"
              onViewModeChange={() => {}}
              onRefresh={fetchListings}
              loading={loading}
            />

            {/* Results Summary */}
            <div className="px-4 py-2 border-b border-border bg-muted/30">
              <div className="flex justify-between items-center text-sm text-muted-foreground" dir="rtl">
                <span>נמצאו {filteredListings.length} מודעות</span>
                <span>מתוך {listings.length} מודעות</span>
              </div>
            </div>

            {/* Listings Table */}
            {loading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin" />
              </div>
            ) : error ? (
              <div className="text-center py-8 text-red-500">
                <p>{error}</p>
                <Button onClick={fetchListings} variant="outline" className="mt-2">
                  נסה שוב
                </Button>
              </div>
            ) : filteredListings.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <p>לא נמצאו מודעות מתאימות</p>
              </div>
            ) : (
              <div className="relative rtl">
                <Table className="rtl">
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-right rtl:text-right">כותרת</TableHead>
                      <TableHead className="text-right rtl:text-right">מחיר</TableHead>
                      <TableHead className="text-right rtl:text-right">חדרים</TableHead>
                      <TableHead className="text-right rtl:text-right">גודל</TableHead>
                      <TableHead className="text-right rtl:text-right">מקור</TableHead>
                      <TableHead className="text-right rtl:text-right">תאריך</TableHead>
                      <TableHead className="text-right rtl:text-right">פעולות</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredListings.map((listing) => (
                      <TableRow key={listing.id} className="hover:bg-muted/50">
                        <TableCell className="text-right rtl:text-right">
                          <div>
                            <p className="font-medium">{listing.title}</p>
                            <p className="text-sm text-muted-foreground">{listing.address}</p>
                          </div>
                        </TableCell>
                        <TableCell className="text-right rtl:text-right font-medium">
                          {formatPrice(listing.price)}
                        </TableCell>
                        <TableCell className="text-right rtl:text-right">
                          {listing.rooms} חדרים
                        </TableCell>
                        <TableCell className="text-right rtl:text-right">
                          {listing.size} מ&quot;ר
                        </TableCell>
                        <TableCell className="text-right rtl:text-right">
                          <Badge className={getSourceColor(listing.source)}>
                            {getSourceDisplay(listing.source)}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right rtl:text-right">
                          {new Date(listing.date_posted).toLocaleDateString('he-IL')}
                        </TableCell>
                        <TableCell className="text-right rtl:text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => window.open(listing.url, '_blank')}
                            className="mr-0 ml-2"
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
        </CardContent>
      </Card>
    </div>
  )
}
