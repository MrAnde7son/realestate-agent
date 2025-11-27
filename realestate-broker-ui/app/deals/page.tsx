'use client'

import React from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { DashboardShell, DashboardHeader } from '@/components/layout/dashboard-shell'
import { SectionHeader, type SectionHeaderAction } from '@/components/layout/section-header'
import { useSavedFilters } from '@/hooks/use-saved-filters'
import { SavedFilterPreset } from '@/components/layout/saved-filters-menu'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogTrigger,
} from '@/components/ui/dialog'
import { apiClient } from '@/lib/api-client'
import {
  DEAL_STAGE_LABELS,
  DEAL_STAGE_ORDER,
  DealAssetSummary,
  DealConfidentiality,
  DealStage,
  DealSummary,
  isActiveStage,
} from '@/lib/deals/types'
import { cn } from '@/lib/utils'
import { Handshake, PlusCircle, RefreshCw, Search, Loader2, MapPin, Users2 } from 'lucide-react'

const currencyFormatter = new Intl.NumberFormat('he-IL', {
  style: 'currency',
  currency: 'ILS',
  maximumFractionDigits: 0,
})

type DealsResponse = {
  deals: DealSummary[]
  fallback?: boolean
  error?: string
}

type StageFilter = 'all' | DealStage

type AssetOption = {
  id: number
  address: string
  city?: string | null
  status?: string | null
  price?: number | null
}

function formatDate(date: string) {
  try {
    return new Date(date).toLocaleDateString('he-IL')
  } catch (error) {
    return date
  }
}

function assetLabel(asset: DealAssetSummary | null | undefined): string {
  if (!asset) return 'נכס ללא פרטים'
  if (asset.address) return asset.address
  if (asset.city) return `${asset.city} • נכס ${asset.id}`
  return `נכס ${asset.id}`
}

function translateStatus(status: string | null | undefined): string {
  if (!status) return ''
  const translations: Record<string, string> = {
    'done': 'מוכן',
    'failed': 'שגיאה',
    'enriching': 'מתעשר',
    'pending': 'ממתין',
    'active': 'פעיל',
    'archived': 'בארכיון',
    'draft': 'טיוטה',
    'processing': 'בעיבוד',
    'syncing': 'מסנכרן נתונים',
    'synced': 'מסונכרן',
    'none': 'ללא סטטוס',
  }
  return translations[status.toLowerCase()] || status
}

function stageBuckets(deals: DealSummary[]) {
  return DEAL_STAGE_ORDER.reduce<Record<DealStage, DealSummary[]>>((acc, stage) => {
    acc[stage] = deals.filter((deal) => deal.stage === stage)
    return acc
  }, {
    discovery: [],
    negotiation: [],
    legal: [],
    financing: [],
    closing: [],
    abandoned: [],
  })
}

export default function DealsPage() {
  const routerRef = React.useRef(useRouter())
  const [deals, setDeals] = React.useState<DealSummary[]>([])
  const [isLoading, setIsLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)
  const [stageFilter, setStageFilter] = React.useState<StageFilter>('all')
  const [search, setSearch] = React.useState('')
  const [debouncedSearch, setDebouncedSearch] = React.useState('')
  const [isRefreshing, setIsRefreshing] = React.useState(false)
  const [isCreateOpen, setIsCreateOpen] = React.useState(false)
  const [selectedAsset, setSelectedAsset] = React.useState<AssetOption | null>(null)
  const [assetSearch, setAssetSearch] = React.useState('')
  const [debouncedAssetSearch, setDebouncedAssetSearch] = React.useState('')
  const [assetResults, setAssetResults] = React.useState<AssetOption[]>([])
  const [assetLoading, setAssetLoading] = React.useState(false)
  const [assetError, setAssetError] = React.useState<string | null>(null)
  const [createStage, setCreateStage] = React.useState<DealStage>('discovery')
  const [createConfidentiality, setCreateConfidentiality] = React.useState<DealConfidentiality>('standard')
  const [isSubmitting, setIsSubmitting] = React.useState(false)
  const [createError, setCreateError] = React.useState<string | null>(null)
  const isLoadingRef = React.useRef(false)
  const { savedFilters, saveFilters, deleteFilter, applyFilter, hasActiveFilters } = useSavedFilters('deals')

  React.useEffect(() => {
    const timer = window.setTimeout(() => {
      setDebouncedSearch(search.trim())
    }, 300)
    return () => window.clearTimeout(timer)
  }, [search])

  React.useEffect(() => {
    const timer = window.setTimeout(() => {
      setDebouncedAssetSearch(assetSearch.trim())
    }, 300)
    return () => window.clearTimeout(timer)
  }, [assetSearch])

  const fallbackMessage = 'שגיאה בטעינת העסקאות'

  const loadDeals = React.useCallback(async () => {
    if (isLoadingRef.current) {
      return
    }
    isLoadingRef.current = true
    setIsRefreshing(true)
    setError(null)
    setIsLoading(true)
    try {
      const params = new URLSearchParams()
      if (stageFilter !== 'all') {
        params.set('stage', stageFilter)
      }
      if (debouncedSearch) {
        params.set('q', debouncedSearch)
      }
      const endpoint = params.size > 0 ? `/api/deals?${params.toString()}` : '/api/deals'
      const response = await apiClient.get<DealsResponse>(endpoint)
      if (!response.ok) {
        // Check for authentication errors
        const data = response.data as any
        if (response.status === 401 || 
            response.error?.includes('Authentication credentials were not provided') ||
            response.error?.includes('Authentication') ||
            data?.detail?.includes('Authentication credentials were not provided')) {
          // Redirect to login with current path as redirect parameter
          routerRef.current.push(`/auth?redirect=${encodeURIComponent('/deals')}`)
          return
        }
        throw new Error(response.error || fallbackMessage)
      }
      const payload = response.data
      setDeals(payload?.deals ?? [])
    } catch (err) {
      console.error('Failed to load deals:', err)
      // Check if error is authentication related
      const errorMessage = err instanceof Error ? err.message : String(err)
      if (errorMessage.includes('Authentication credentials were not provided') ||
          errorMessage.includes('Authentication') ||
          (typeof err === 'object' && err !== null && 'detail' in err && 
           typeof (err as any).detail === 'string' && 
           (err as any).detail.includes('Authentication credentials were not provided'))) {
        routerRef.current.push(`/auth?redirect=${encodeURIComponent('/deals')}`)
        return
      }
      setDeals([])
      setError(fallbackMessage)
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
      isLoadingRef.current = false
    }
  }, [stageFilter, debouncedSearch])

  React.useEffect(() => {
    loadDeals()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stageFilter, debouncedSearch])

  React.useEffect(() => {
    if (!debouncedAssetSearch) {
      setAssetResults([])
      setAssetError(null)
      return
    }

    let ignore = false
    setAssetLoading(true)
    setAssetError(null)
    ;(async () => {
      const query = new URLSearchParams({ search: debouncedAssetSearch, limit: '6' })
      const response = await apiClient.get(`/api/assets?${query.toString()}`)
      if (!response.ok) {
        // Check for authentication errors
        const data = response.data as any
        if (response.status === 401 || 
            response.error?.includes('Authentication credentials were not provided') ||
            response.error?.includes('Authentication') ||
            data?.detail?.includes('Authentication credentials were not provided')) {
          // Redirect to login with current path as redirect parameter
          routerRef.current.push(`/auth?redirect=${encodeURIComponent('/deals')}`)
          return
        }
        setAssetError(response.error || 'שגיאה בטעינת נכסים')
        setAssetResults([])
        setAssetLoading(false)
        return
      }
      if (ignore) {
        return
      }
      const rows = (response.data?.rows ?? []) as any[]
      const normalized: AssetOption[] = rows.map((row) => ({
        id: row.id,
        address: row.address || row.normalizedAddress || `נכס ${row.id}`,
        city: row.city ?? null,
        status: row.status ?? null,
        price: row.price ?? null,
      }))
      setAssetResults(normalized)
      setAssetLoading(false)
    })().catch((err) => {
      console.error('Asset search failed:', err)
      // Check if error is authentication related
      const errorMessage = err instanceof Error ? err.message : String(err)
      if (errorMessage.includes('Authentication credentials were not provided') ||
          errorMessage.includes('Authentication') ||
          (typeof err === 'object' && err !== null && 'detail' in err && 
           typeof (err as any).detail === 'string' && 
           (err as any).detail.includes('Authentication credentials were not provided'))) {
        routerRef.current.push(`/auth?redirect=${encodeURIComponent('/deals')}`)
        return
      }
      setAssetError('שגיאה בטעינת נכסים')
      setAssetResults([])
      setAssetLoading(false)
    })

    return () => {
      ignore = true
    }
  }, [debouncedAssetSearch])

  const totalDeals = deals.length
  const activeDeals = deals.filter((deal) => isActiveStage(deal.stage)).length
  const potentialVolume = deals.reduce((sum, deal) => sum + (deal.asset_summary?.price ?? 0), 0)

  const grouped = React.useMemo(() => stageBuckets(deals), [deals])

  // Build current filter state for saving
  const buildCurrentFilters = React.useCallback(() => {
    return {
      stageFilter,
      search: debouncedSearch,
    };
  }, [stageFilter, debouncedSearch]);

  // Handle save current filters
  const handleSaveCurrentFilters = React.useCallback(() => {
    const currentFilters = buildCurrentFilters();
    const filterCount = Object.values(currentFilters).filter(v => 
      v !== undefined && v !== null && v !== '' && v !== 'all'
    ).length;
    
    if (filterCount === 0) {
      return;
    }

    const label = stageFilter !== 'all' ? `שלב: ${DEAL_STAGE_LABELS[stageFilter].label}` : `חיפוש: ${debouncedSearch || 'כללי'}`;
    saveFilters(currentFilters, label);
  }, [buildCurrentFilters, saveFilters, stageFilter, debouncedSearch]);

  // Apply saved filter
  const handleApplyFilter = React.useCallback((filterData: Record<string, any>) => {
    if (filterData.stageFilter !== undefined) setStageFilter(filterData.stageFilter || 'all');
    if (filterData.search !== undefined) setSearch(filterData.search || '');
  }, []);

  // Convert saved filters to presets
  const savedFilterPresets: SavedFilterPreset[] = React.useMemo(() => {
    return savedFilters.map((filter) => ({
      id: filter.id,
      label: filter.label,
      description: filter.description,
      isActive: false,
      isStarred: filter.isStarred,
      onClick: () => {
        applyFilter(filter.id, handleApplyFilter);
      },
      onDelete: () => {
        deleteFilter(filter.id);
      },
    }));
  }, [savedFilters, applyFilter, handleApplyFilter, deleteFilter]);

  const hasActiveFiltersValue = React.useMemo(() => {
    return hasActiveFilters(buildCurrentFilters());
  }, [hasActiveFilters, buildCurrentFilters]);

  const handleCreateDeal = async () => {
    if (!selectedAsset) {
      setCreateError('בחרו נכס כדי לפתוח עסקה')
      return
    }
    setIsSubmitting(true)
    setCreateError(null)
    const payload = {
      assetId: selectedAsset.id,
      stage: createStage,
      confidentialityLevel: createConfidentiality,
      parties: [],
    }
    const response = await apiClient.post('/api/deals', payload)
    if (!response.ok) {
      // Check for authentication errors
      const data = response.data as any
      if (response.status === 401 || 
          response.error?.includes('Authentication credentials were not provided') ||
            response.error?.includes('Authentication') ||
            data?.detail?.includes('Authentication credentials were not provided')) {
        // Redirect to login with current path as redirect parameter
        routerRef.current.push(`/auth?redirect=${encodeURIComponent('/deals')}`)
        return
      }
      setCreateError(response.error || 'שגיאה ביצירת העסקה')
      setIsSubmitting(false)
      return
    }
    setIsSubmitting(false)
    setIsCreateOpen(false)
    setSelectedAsset(null)
    setAssetSearch('')
    setAssetResults([])
    await loadDeals()
  }

  const renderDealCard = (deal: DealSummary) => {
    const asset = deal.asset_summary
    const buyerCount = deal.party_roles.filter((role) => role.side === 'buyer').length
    const sellerCount = deal.party_roles.filter((role) => role.side === 'seller').length
    const neutralCount = deal.party_roles.filter((role) => role.side === 'neutral').length

    return (
      <Card key={deal.id} className='border-muted bg-card/60 shadow-sm transition-all hover:shadow-md hover:border-primary/20'>
        <CardHeader className='gap-2 pb-3'>
          <div className='flex items-center justify-between gap-2'>
            <div className='flex flex-col gap-1 min-w-0 flex-1'>
              <CardTitle className='text-base font-semibold truncate'>{assetLabel(asset)}</CardTitle>
              <CardDescription className='flex items-center gap-2 text-xs text-muted-foreground flex-wrap'>
                <span className='flex items-center gap-1 shrink-0'><MapPin className='h-3 w-3' />{asset?.city || 'ללא עיר'}</span>
                <span className='shrink-0'>עודכן {formatDate(deal.updated_at)}</span>
              </CardDescription>
            </div>
            <Badge variant='outline' className='shrink-0'>{DEAL_STAGE_LABELS[deal.stage].label}</Badge>
          </div>
        </CardHeader>
        <CardContent className='space-y-3 text-sm pt-0'>
          <div className='flex flex-wrap gap-2 text-muted-foreground'>
            {typeof asset?.price === 'number' && asset.price > 0 ? (
              <Badge variant='secondary' className='flex items-center gap-1'>
                <Handshake className='h-3 w-3' />
                {currencyFormatter.format(asset.price)}
              </Badge>
            ) : null}
            {asset?.status ? (
              <Badge variant='secondary'>{translateStatus(asset.status)}</Badge>
            ) : null}
            {asset?.building_type ? (
              <Badge variant='secondary'>{asset.building_type}</Badge>
            ) : null}
          </div>
          <div className='flex flex-wrap items-center gap-3 text-xs text-muted-foreground'>
            <span className='flex items-center gap-1'><Users2 className='h-3 w-3' />צד קונה: {buyerCount}</span>
            <span className='flex items-center gap-1'>צד מוכר: {sellerCount}</span>
            {neutralCount > 0 ? <span className='flex items-center gap-1'>צדדים נוספים: {neutralCount}</span> : null}
          </div>
          <div className='flex flex-wrap gap-2 pt-1'>
            <Link href={`/assets/${deal.asset}/deal?from=deals`}>
              <Button size='sm' variant='default' className='w-full sm:w-auto'>מרחב עסקה</Button>
            </Link>
            <Link href={`/assets/${deal.asset}`}>
              <Button size='sm' variant='outline' className='w-full sm:w-auto'>פרטי נכס</Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    )
  }

  const renderStageColumn = (stage: DealStage) => {
    const dealsForStage = grouped[stage]
    const meta = DEAL_STAGE_LABELS[stage]
    const isAbandoned = stage === 'abandoned'
    return (
      <Card key={stage} className={cn(
        'flex h-full flex-col border transition-all hover:shadow-md',
        isAbandoned ? 'border-muted/50 bg-muted/20' : 'border-dashed border-muted bg-card'
      )}>
        <CardHeader className='space-y-2 pb-3'>
          <div className='flex items-center justify-between gap-2'>
            <CardTitle className='text-sm font-semibold'>{meta.label}</CardTitle>
            <Badge variant={dealsForStage.length > 0 ? 'default' : 'secondary'} className='min-w-[2rem] justify-center'>
              {dealsForStage.length}
            </Badge>
          </div>
          <CardDescription className='text-xs text-muted-foreground leading-relaxed'>{meta.description}</CardDescription>
        </CardHeader>
        <CardContent className='flex flex-1 flex-col gap-3 pt-0'>
          {isLoading && dealsForStage.length === 0 ? (
            <div className='space-y-3'>
              <Skeleton className='h-20 w-full rounded-lg' />
              <Skeleton className='h-20 w-full rounded-lg' />
            </div>
          ) : dealsForStage.length === 0 ? (
            <p className='text-xs text-muted-foreground text-center py-4'>אין עסקאות בשלב זה כרגע.</p>
          ) : (
            dealsForStage.map(renderDealCard)
          )}
        </CardContent>
      </Card>
    )
  }

  return (
    <DashboardLayout>
      <DashboardShell>
        <SectionHeader
          title='עסקאות ותהליכי סגירה'
          description='תצוגה מרוכזת של כל העסקאות הפעילות וההזדמנויות שבדרך לסגירה'
          count={totalDeals}
          countLabel="עסקאות"
          savedFilterPresets={savedFilterPresets}
          onSaveCurrentFilters={handleSaveCurrentFilters}
          hasActiveFilters={hasActiveFiltersValue}
          primaryActions={[
            {
              label: 'רענון',
              onClick: () => loadDeals(),
              icon: isRefreshing ? <Loader2 className='mr-2 h-4 w-4 animate-spin' /> : <RefreshCw className='mr-2 h-4 w-4' />,
              variant: 'outline',
              size: 'sm',
              disabled: isRefreshing,
            },
          ]}
        >
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button size='sm' className='h-8 sm:min-h-[44px] rounded-full px-2 sm:px-4 flex items-center gap-1 sm:gap-2 flex-shrink-0 text-xs sm:text-sm'>
                <PlusCircle className='mr-2 h-4 w-4' />
                פתיחת עסקה חדשה
              </Button>
            </DialogTrigger>
              <DialogContent className='sm:max-w-lg'>
                <DialogHeader>
                  <DialogTitle>פתיחת מרחב עסקה חדש</DialogTitle>
                  <DialogDescription>
                    בחרו נכס קיים וקבעו את שלב הפתיחה ורמת הסודיות. ניתן לעדכן פרטים לאחר מכן במרחב העסקה.
                  </DialogDescription>
                </DialogHeader>
                <div className='space-y-4 py-2'>
                  <div className='space-y-2'>
                    <label className='text-sm font-medium text-muted-foreground'>חיפוש נכס</label>
                    <div className='relative'>
                      <Search className='absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground' />
                      <Input
                        value={assetSearch}
                        onChange={(event) => setAssetSearch(event.target.value)}
                        placeholder='כתובת, עיר או מזהה נכס'
                        className='pr-9'
                      />
                    </div>
                    {assetError ? <p className='text-xs text-destructive'>{assetError}</p> : null}
                    <div className='max-h-48 space-y-2 overflow-y-auto rounded-md border bg-muted/30 p-2'>
                      {assetLoading ? (
                        <div className='space-y-2'>
                          <Skeleton className='h-10 w-full rounded-md' />
                          <Skeleton className='h-10 w-full rounded-md' />
                        </div>
                      ) : assetResults.length === 0 ? (
                        <p className='text-xs text-muted-foreground'>התחילו להקליד כדי למצוא נכס רשום.</p>
                      ) : (
                        assetResults.map((option) => (
                          <button
                            key={option.id}
                            type='button'
                            onClick={() => setSelectedAsset(option)}
                            className={cn(
                              'flex w-full flex-col gap-1 rounded-md border p-2 text-right text-sm transition-colors',
                              selectedAsset?.id === option.id
                                ? 'border-primary bg-primary/10'
                                : 'border-transparent bg-background hover:border-muted'
                            )}
                          >
                            <span className='font-medium'>{option.address}</span>
                            <span className='text-xs text-muted-foreground'>
                              {option.city ? `${option.city} • ` : ''}מזהה #{option.id}
                            </span>
                          </button>
                        ))
                      )}
                    </div>
                    {selectedAsset ? (
                      <div className='rounded-md border border-dashed bg-muted/20 p-3 text-xs'>
                        <p className='font-medium'>נכס שנבחר</p>
                        <p>{selectedAsset.address}</p>
                        <p className='text-muted-foreground'>מזהה #{selectedAsset.id}</p>
                      </div>
                    ) : null}
                  </div>
                  <div className='grid gap-3 sm:grid-cols-2'>
                    <div className='space-y-2'>
                      <label className='text-sm font-medium text-muted-foreground'>שלב פתיחה</label>
                      <div className='flex flex-wrap gap-2'>
                        {['discovery', 'negotiation', 'legal', 'financing', 'closing'].map((stage) => (
                          <Button
                            key={stage}
                            type='button'
                            size='sm'
                            variant={createStage === stage ? 'default' : 'outline'}
                            onClick={() => setCreateStage(stage as DealStage)}
                          >
                            {DEAL_STAGE_LABELS[stage as DealStage].label}
                          </Button>
                        ))}
                      </div>
                    </div>
                    <div className='space-y-2'>
                      <label className='text-sm font-medium text-muted-foreground'>רמת סודיות</label>
                      <div className='flex flex-wrap gap-2'>
                        {[
                          { value: 'standard', label: 'רגיל' },
                          { value: 'restricted', label: 'מוגבל' },
                          { value: 'internal', label: 'פנימי' },
                        ].map((item) => (
                          <Button
                            key={item.value}
                            type='button'
                            size='sm'
                            variant={createConfidentiality === item.value ? 'default' : 'outline'}
                            onClick={() => setCreateConfidentiality(item.value as DealConfidentiality)}
                          >
                            {item.label}
                          </Button>
                        ))}
                      </div>
                    </div>
                  </div>
                  {createError ? <p className='text-xs text-destructive'>{createError}</p> : null}
                </div>
                <DialogFooter>
                  <Button variant='outline' onClick={() => setIsCreateOpen(false)} disabled={isSubmitting}>
                    ביטול
                  </Button>
                  <Button onClick={handleCreateDeal} disabled={isSubmitting}>
                    {isSubmitting ? <Loader2 className='mr-2 h-4 w-4 animate-spin' /> : null}
                    פתיחת עסקה
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
        </SectionHeader>

        <section className='space-y-6'>
          <Card className='border-muted bg-card/70'>
            <CardContent className='flex flex-col gap-4 pt-6 md:flex-row md:items-center md:justify-between'>
              <div className='flex flex-col gap-2'>
                <div className='flex items-center gap-2 text-sm text-muted-foreground'>
                  <Handshake className='h-5 w-5 text-primary' />
                  סקירת צבר העסקאות הפעילות שלכם
                </div>
                <div className='flex flex-wrap gap-4 text-sm'>
                  <span>סה״כ עסקאות: <strong>{totalDeals}</strong></span>
                  <span>עסקאות פעילות: <strong>{activeDeals}</strong></span>
                  <span>
                    שווי פוטנציאלי: <strong>{currencyFormatter.format(potentialVolume)}</strong>
                  </span>
                </div>
              </div>
              <div className='flex flex-wrap items-center gap-2'>
                <div className='relative'>
                  <Search className='absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground' />
                  <Input
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder='חיפוש לפי נכס, עיר או סטטוס'
                    className='w-64 pr-9'
                  />
                </div>
                <div className='flex flex-wrap gap-2'>
                  {[{ value: 'all', label: 'כל השלבים' }, ...DEAL_STAGE_ORDER.map((stage) => ({
                    value: stage,
                    label: DEAL_STAGE_LABELS[stage].label,
                  }))].map((item) => (
                    <Button
                      key={item.value}
                      variant={stageFilter === item.value ? 'default' : 'outline'}
                      size='sm'
                      onClick={() => setStageFilter(item.value as StageFilter)}
                    >
                      {item.label}
                    </Button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {error ? (
            <Card className='border-destructive/40 bg-destructive/10'>
              <CardContent className='py-6 text-sm text-destructive'>
                {error}
              </CardContent>
            </Card>
          ) : null}

          <div className='grid gap-4 sm:grid-cols-2 lg:grid-cols-3'>
            {DEAL_STAGE_ORDER.map(renderStageColumn)}
          </div>
        </section>
      </DashboardShell>
    </DashboardLayout>
  )
}
