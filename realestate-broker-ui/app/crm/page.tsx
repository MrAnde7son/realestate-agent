'use client';

import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/Card';
import { CheckCircle, XCircle } from 'lucide-react';
import { Lead, Contact, CrmApi } from '@/lib/api/crm';
import DashboardLayout from '@/components/layout/dashboard-layout';
import { SectionHeader } from '@/components/layout/section-header';
import { useToast } from '@/hooks/use-toast';
import { PageLoader } from '@/components/ui/page-loader';
import { useAuth } from '@/lib/auth-context';
import { useAnalytics } from '@/hooks/useAnalytics';
import { CombinedCrmTable } from '@/components/crm/combined-crm-table';

export default function CrmUnifiedPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();
  const { user, isLoading: authLoading } = useAuth();
  const canAccessCrm = ['broker', 'appraiser', 'admin'].includes(user?.role || '');
  const { trackEvent } = useAnalytics();
  const hasTrackedOpen = useRef(false);

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

  const refreshData = useCallback(async () => {
    await Promise.all([loadContacts(), loadLeads()]);
  }, [loadContacts, loadLeads]);

  const loadInitialData = useCallback(async () => {
    try {
      setIsLoading(true);
      await refreshData();
    } finally {
      setIsLoading(false);
    }
  }, [refreshData]);

  useEffect(() => {
    if (authLoading) {
      return;
    }

    if (!canAccessCrm) {
      setIsLoading(false);
      return;
    }

    void loadInitialData();
  }, [authLoading, canAccessCrm, loadInitialData]);

  useEffect(() => {
    if (!authLoading && canAccessCrm && !hasTrackedOpen.current) {
      trackEvent({
        event: 'crm_opened',
        meta: { view: 'combined' },
      });
      hasTrackedOpen.current = true;
    }
  }, [authLoading, canAccessCrm, trackEvent]);

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
      <div className="w-full p-3 sm:p-6 space-y-6 px-4 sm:px-6 lg:px-8">
        <SectionHeader
          title="ניהול לקוחות ולידים"
          description="ניהול לקוחות, מעקב לידים ושליחת דוחות ממותגים"
          count={contacts.length}
          countLabel="לקוחות"
        />

        {/* Key Metrics - Success & Failure Only */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 rtl:flex-row-reverse">
              <CardTitle className="text-base font-medium rtl:text-start">נסגרו בהצלחה</CardTitle>
              <CheckCircle className="h-5 w-5 text-green-600" />
            </CardHeader>
            <CardContent className="rtl:text-start">
              <div className="text-2xl sm:text-3xl font-bold text-green-600">{stats.closedWon}</div>
              <p className="text-sm text-muted-foreground mt-1">עסקאות שהושלמו</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 rtl:flex-row-reverse">
              <CardTitle className="text-base font-medium rtl:text-start">נסגרו ללא הצלחה</CardTitle>
              <XCircle className="h-5 w-5 text-red-600" />
            </CardHeader>
            <CardContent className="rtl:text-start">
              <div className="text-2xl sm:text-3xl font-bold text-red-600">{stats.closedLost}</div>
              <p className="text-sm text-muted-foreground mt-1">לידים שלא התממשו</p>
            </CardContent>
          </Card>
        </div>

        <CombinedCrmTable contacts={contacts} leads={leads} onRefresh={refreshData} />
      </div>
    </DashboardLayout>
  );
}
