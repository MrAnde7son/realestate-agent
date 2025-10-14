'use client';

import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/Card';
import { Users, TrendingUp, CheckCircle, XCircle, ArrowRight } from 'lucide-react';
import { Lead, Contact, CrmApi } from '@/lib/api/crm';
import Link from 'next/link';
import DashboardLayout from '@/components/layout/dashboard-layout';
import { useToast } from '@/hooks/use-toast';
import { PageLoader } from '@/components/ui/page-loader';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/Badge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import LeadsList from '@/components/crm/LeadsList';
import ContactsList from '@/components/crm/ContactsList';
import { useAuth } from '@/lib/auth-context';
import { useAnalytics } from '@/hooks/useAnalytics';

export default function CrmUnifiedPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();
  const { user, isLoading: authLoading } = useAuth();
  const canAccessCrm = ['broker', 'appraiser', 'admin'].includes(user?.role || '');
  const searchParams = useSearchParams();
  const router = useRouter();
  const { trackEvent } = useAnalytics();
  const hasTrackedOpen = useRef(false);

  const tabParam = searchParams?.get('tab');
  const tab: 'leads' | 'clients' = tabParam === 'leads' ? 'leads' : 'clients';

  const setTab = useCallback(
    (nextTab: 'leads' | 'clients') => {
      const params = new URLSearchParams(searchParams?.toString());
      if (params.get('tab') === nextTab) {
        // Still fire analytics to capture the intent even if tab didn't change
        trackEvent({
          event: 'crm_tab_changed',
          meta: { tab: nextTab },
        });
        return;
      }
      params.set('tab', nextTab);
      const query = params.toString();
      router.replace(query ? `/crm?${query}` : '/crm');
      trackEvent({
        event: 'crm_tab_changed',
        meta: { tab: nextTab },
      });
    },
    [router, searchParams, trackEvent]
  );

  const handleCardClick = useCallback(
    (target: 'leads' | 'clients') => {
      trackEvent({
        event: 'crm_card_clicked',
        meta: { target },
      });
      setTab(target);
    },
    [setTab, trackEvent]
  );

  const loadContacts = useCallback(async () => {
    try {
      const data = await CrmApi.getContacts();
      setContacts(data);
    } catch (error: any) {
      console.error('Failed to load contacts:', error);
      if (error.message?.includes('authentication') || error.message?.includes('token')) {
        toast({
          title: 'נדרשת התחברות',
          description: 'אנא התחבר למערכת כדי לגשת לניהול לקוחות',
          variant: 'destructive',
        });
      } else {
        toast({
          title: 'שגיאה',
          description: 'לא ניתן לטעון את רשימת הלקוחות',
          variant: 'destructive',
        });
      }
    }
  }, [toast]);

  const loadLeads = useCallback(async () => {
    try {
      const data = await CrmApi.getLeads();
      setLeads(data);
    } catch (error: any) {
      console.error('Failed to load leads:', error);
      if (error.message?.includes('authentication') || error.message?.includes('token')) {
        toast({
          title: 'נדרשת התחברות',
          description: 'אנא התחבר למערכת כדי לגשת לניהול לידים',
          variant: 'destructive',
        });
      } else {
        toast({
          title: 'שגיאה',
          description: 'לא ניתן לטעון את רשימת הלידים',
          variant: 'destructive',
        });
      }
    }
  }, [toast]);

  const loadAllData = useCallback(async () => {
    try {
      setIsLoading(true);
      await Promise.all([loadContacts(), loadLeads()]);
    } finally {
      setIsLoading(false);
    }
  }, [loadContacts, loadLeads]);

  useEffect(() => {
    if (authLoading) {
      return;
    }

    if (!canAccessCrm) {
      setIsLoading(false);
      return;
    }

    loadAllData();
  }, [authLoading, canAccessCrm, loadAllData]);

  useEffect(() => {
    if (!authLoading && canAccessCrm && !hasTrackedOpen.current) {
      trackEvent({
        event: 'crm_opened',
        meta: { tab },
      });
      hasTrackedOpen.current = true;
    }
  }, [authLoading, canAccessCrm, trackEvent, tab]);

  const stats = useMemo(() => {
    const totalLeads = leads.length;
    const newLeads = leads.filter((lead) => lead.status === 'new').length;
    const activeLeads = leads.filter((lead) =>
      ['contacted', 'interested', 'negotiating'].includes(lead.status)
    ).length;
    const closedWon = leads.filter((lead) => lead.status === 'closed-won').length;
    const closedLost = leads.filter((lead) => lead.status === 'closed-lost').length;

    return {
      totalLeads,
      newLeads,
      activeLeads,
      closedWon,
      closedLost,
      conversionRate: totalLeads > 0 ? Math.round((closedWon / totalLeads) * 100) : 0,
    };
  }, [leads]);

  const recentLeads = useMemo(
    () =>
      [...leads]
        .sort(
          (a, b) =>
            new Date(b.last_activity_at).getTime() - new Date(a.last_activity_at).getTime()
        )
        .slice(0, 5),
    [leads]
  );

  if (authLoading || (isLoading && canAccessCrm)) {
    return (
      <DashboardLayout>
        <PageLoader message="טוען נתוני לקוחות..." showLogo={false} />
      </DashboardLayout>
    );
  }

  if (!authLoading && !canAccessCrm) {
    return (
      <DashboardLayout>
        <div className="p-6">
          <Card>
            <CardHeader>
              <CardTitle>גישה מוגבלת</CardTitle>
              <CardDescription>
                מודול הלקוחות זמין למשתמשים מסוג מתווך או שמאי בלבד.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p>
                אנא עדכן את סוג המשתמש שלך או צור קשר עם התמיכה אם ברצונך לקבל גישה לניהול לקוחות ולידים.
              </p>
            </CardContent>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="container mx-auto p-3 sm:p-6 space-y-6">
        <div className="mb-2 sm:mb-4">
          <h1 className="text-2xl sm:text-3xl font-bold mb-2 rtl:text-right">ניהול לקוחות ולידים</h1>
          <p className="text-muted-foreground text-sm sm:text-base rtl:text-right">
            ניהול לקוחות, מעקב לידים ושליחת דוחות ממותגים
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
          <Card className="cursor-pointer" onClick={() => handleCardClick('leads')}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 rtl:flex-row-reverse">
              <CardTitle className="text-sm font-medium rtl:text-right">לידים</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent className="rtl:text-right">
              <div className="text-xl sm:text-2xl font-bold">{stats.totalLeads}</div>
              <p className="text-xs text-muted-foreground">{stats.newLeads} חדשים</p>
            </CardContent>
          </Card>

          <Card className="cursor-pointer" onClick={() => handleCardClick('clients')}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 rtl:flex-row-reverse">
              <CardTitle className="text-sm font-medium rtl:text-right">לקוחות</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent className="rtl:text-right">
              <div className="text-xl sm:text-2xl font-bold">{contacts.length}</div>
              <p className="text-xs text-muted-foreground">לקוחות רשומים</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 rtl:flex-row-reverse">
              <CardTitle className="text-sm font-medium rtl:text-right">המרה</CardTitle>
              <CheckCircle className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent className="rtl:text-right">
              <div className="text-xl sm:text-2xl font-bold text-green-600">{stats.conversionRate}%</div>
              <p className="text-xs text-muted-foreground">{stats.closedWon} נסגרו בהצלחה</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 rtl:flex-row-reverse">
              <CardTitle className="text-sm font-medium rtl:text-right">נסגרו ללא הצלחה</CardTitle>
              <XCircle className="h-4 w-4 text-red-600" />
            </CardHeader>
            <CardContent className="rtl:text-right">
              <div className="text-xl sm:text-2xl font-bold text-red-600">{stats.closedLost}</div>
              <p className="text-xs text-muted-foreground">לא התממשו</p>
            </CardContent>
          </Card>
        </div>

        <Tabs value={tab} onValueChange={(value) => setTab(value as 'leads' | 'clients')} className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="leads">לידים</TabsTrigger>
            <TabsTrigger value="clients">לקוחות</TabsTrigger>
          </TabsList>
          
          <TabsContent value="leads" className="space-y-6">
            <LeadsList onConvertedToClient={() => setTab('clients')} />
          </TabsContent>
          
          <TabsContent value="clients" className="space-y-6">
            <ContactsList />
          </TabsContent>
        </Tabs>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
          <Card>
            <CardHeader className="rtl:text-right">
              <CardTitle className="text-base sm:text-lg">לידים אחרונים</CardTitle>
              <CardDescription className="text-sm">פעילות אחרונה במערכת</CardDescription>
            </CardHeader>
            <CardContent>
              {recentLeads.length === 0 ? (
                <div className="text-center py-4 text-muted-foreground rtl:text-right">
                  אין לידים עדיין
                </div>
              ) : (
                <div className="space-y-3">
                  {recentLeads.map((lead) => (
                    <div
                      key={lead.id}
                      className="flex items-center justify-between p-2 sm:p-3 bg-gray-50 rounded-lg rtl:flex-row-reverse"
                    >
                      <div className="flex-1 rtl:text-right min-w-0">
                        <div className="font-medium text-sm sm:text-base truncate">
                          {lead.contact.name}
                        </div>
                        <div className="text-xs sm:text-sm text-muted-foreground truncate">
                          {lead.asset_address}
                        </div>
                      </div>
                      <div className="flex items-center gap-1 sm:gap-2 rtl:flex-row-reverse flex-shrink-0">
                        <Badge variant="outline" className="text-xs">
                          {lead.status === 'new' && 'חדש'}
                          {lead.status === 'contacted' && 'יצרתי קשר'}
                          {lead.status === 'interested' && 'מתעניין'}
                          {lead.status === 'negotiating' && 'במשא ומתן'}
                          {lead.status === 'closed-won' && 'נסגר בהצלחה'}
                          {lead.status === 'closed-lost' && 'נסגר ללא הצלחה'}
                        </Badge>
                        <Link href="/crm/leads">
                          <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                            <ArrowRight className="h-3 w-3" />
                          </Button>
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {stats.totalLeads > 0 && (
          <Card>
            <CardHeader className="rtl:text-right">
              <CardTitle className="text-base sm:text-lg">התפלגות סטטוסים</CardTitle>
              <CardDescription className="text-sm">פילוח הלידים לפי סטטוס</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
                <div className="text-center">
                  <div className="text-lg sm:text-2xl font-bold text-blue-600">{stats.newLeads}</div>
                  <div className="text-xs sm:text-sm text-muted-foreground">חדשים</div>
                </div>
                <div className="text-center">
                  <div className="text-lg sm:text-2xl font-bold text-yellow-600">
                    {leads.filter((l) => l.status === 'contacted').length}
                  </div>
                  <div className="text-xs sm:text-sm text-muted-foreground">יצרתי קשר</div>
                </div>
                <div className="text-center">
                  <div className="text-lg sm:text-2xl font-bold text-orange-600">
                    {leads.filter((l) => l.status === 'interested').length}
                  </div>
                  <div className="text-xs sm:text-sm text-muted-foreground">מתעניינים</div>
                </div>
                <div className="text-center">
                  <div className="text-lg sm:text-2xl font-bold text-purple-600">
                    {leads.filter((l) => l.status === 'negotiating').length}
                  </div>
                  <div className="text-xs sm:text-sm text-muted-foreground">במשא ומתן</div>
                </div>
                <div className="text-center">
                  <div className="text-lg sm:text-2xl font-bold text-green-600">{stats.closedWon}</div>
                  <div className="text-xs sm:text-sm text-muted-foreground">נסגרו בהצלחה</div>
                </div>
                <div className="text-center">
                  <div className="text-lg sm:text-2xl font-bold text-red-600">{stats.closedLost}</div>
                  <div className="text-xs sm:text-sm text-muted-foreground">נסגרו ללא הצלחה</div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}
