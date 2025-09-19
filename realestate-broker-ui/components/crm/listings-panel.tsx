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
  }, [assetId, assetAddress])

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

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-right">מודעות דומות</CardTitle>
          <p className="text-sm text-muted-foreground text-right">
            מודעות נדלן דומות מהאתרים השונים
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Search and Filters */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-right block">חיפוש</label>
              <div className="relative">
                <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  placeholder="חיפוש במודעות..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pr-10 text-right"
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-right block">מחיר מינימלי</label>
              <Input
                placeholder="0"
                value={priceRange.min}
                onChange={(e) => setPriceRange(prev => ({ ...prev, min: e.target.value }))}
                type="number"
                className="text-right"
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-right block">מחיר מקסימלי</label>
              <Input
                placeholder="10000000"
                value={priceRange.max}
                onChange={(e) => setPriceRange(prev => ({ ...prev, max: e.target.value }))}
                type="number"
                className="text-right"
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-right block">חדרים</label>
              <Select value={roomsFilter} onValueChange={setRoomsFilter}>
                <SelectTrigger className="text-right">
                  <SelectValue placeholder="כל החדרים" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">כל החדרים</SelectItem>
                  <SelectItem value="1">1 חדר</SelectItem>
                  <SelectItem value="2">2 חדרים</SelectItem>
                  <SelectItem value="3">3 חדרים</SelectItem>
                  <SelectItem value="4">4 חדרים</SelectItem>
                  <SelectItem value="5">5+ חדרים</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-right block">סוג נכס</label>
              <Select value={propertyTypeFilter} onValueChange={setPropertyTypeFilter}>
                <SelectTrigger className="text-right">
                  <SelectValue placeholder="כל הסוגים" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">כל הסוגים</SelectItem>
                  <SelectItem value="דירה">דירה</SelectItem>
                  <SelectItem value="בית פרטי">בית פרטי</SelectItem>
                  <SelectItem value="נטהאוז">נטהאוז</SelectItem>
                  <SelectItem value="דופלקס">דופלקס</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-right block">מקור</label>
              <Select value={sourceFilter} onValueChange={setSourceFilter}>
                <SelectTrigger className="text-right">
                  <SelectValue placeholder="כל המקורות" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">כל המקורות</SelectItem>
                  <SelectItem value="yad2">יד2</SelectItem>
                  <SelectItem value="madlan">מדלן</SelectItem>
                  <SelectItem value="homeless">Homeless</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex items-end">
              <Button 
                onClick={fetchListings} 
                disabled={loading}
                variant="outline"
                className="w-full"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
                רענן
              </Button>
            </div>
          </div>

          {/* Results Summary */}
          <div className="flex justify-between items-center text-sm text-muted-foreground">
            <span>נמצאו {filteredListings.length} מודעות</span>
            <span>מתוך {listings.length} מודעות</span>
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
            <div className="border rounded-lg">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-right">כותרת</TableHead>
                    <TableHead className="text-right">מחיר</TableHead>
                    <TableHead className="text-right">חדרים</TableHead>
                    <TableHead className="text-right">גודל</TableHead>
                    <TableHead className="text-right">מקור</TableHead>
                    <TableHead className="text-right">תאריך</TableHead>
                    <TableHead className="text-right">פעולות</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredListings.map((listing) => (
                    <TableRow key={listing.id}>
                      <TableCell className="text-right">
                        <div>
                          <p className="font-medium">{listing.title}</p>
                          <p className="text-sm text-muted-foreground">{listing.address}</p>
                        </div>
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {formatPrice(listing.price)}
                      </TableCell>
                      <TableCell className="text-right">
                        {listing.rooms} חדרים
                      </TableCell>
                      <TableCell className="text-right">
                        {listing.size} מ"ר
                      </TableCell>
                      <TableCell className="text-right">
                        <Badge className={getSourceColor(listing.source)}>
                          {getSourceDisplay(listing.source)}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        {new Date(listing.date_posted).toLocaleDateString('he-IL')}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => window.open(listing.url, '_blank')}
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
        </CardContent>
      </Card>
    </div>
  )
}
