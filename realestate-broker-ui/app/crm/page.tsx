'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { 
  Users, 
  TrendingUp, 
  Clock, 
  CheckCircle, 
  XCircle,
  ArrowRight,
  Plus
} from 'lucide-react';
import { Lead, Contact, CrmApi } from '@/lib/api/crm';
import Link from 'next/link';
import DashboardLayout from '@/components/layout/dashboard-layout';
import { useToast } from '@/hooks/use-toast';
import { PageLoader } from '@/components/ui/page-loader';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/Badge';
import { LeadStatusBadge } from '@/components/crm/lead-status-badge';
import { useAuth } from '@/lib/auth-context';

export default function CrmPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();
  const { user, isLoading: authLoading } = useAuth();
  const canAccessCrm = ['broker', 'appraiser', 'admin'].includes(user?.role || '');

  const loadContacts = useCallback(async () => {
    try {
      const data = await CrmApi.getContacts();
      setContacts(data);
    } catch (error: any) {
      console.error('Failed to load contacts:', error);
      if (error.message.includes('authentication') || error.message.includes('token')) {
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
      if (error.message.includes('authentication') || error.message.includes('token')) {
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

  const getStats = () => {
    const totalLeads = leads.length;
    const newLeads = leads.filter(lead => lead.status === 'new').length;
    const activeLeads = leads.filter(lead => 
      ['contacted', 'interested', 'negotiating'].includes(lead.status)
    ).length;
    const closedWon = leads.filter(lead => lead.status === 'closed-won').length;
    const closedLost = leads.filter(lead => lead.status === 'closed-lost').length;

    return {
      totalLeads,
      newLeads,
      activeLeads,
      closedWon,
      closedLost,
      conversionRate: totalLeads > 0 ? Math.round((closedWon / totalLeads) * 100) : 0
    };
  };

  const getRecentLeads = () => {
    return leads
      .sort((a, b) => new Date(b.last_activity_at).getTime() - new Date(a.last_activity_at).getTime())
      .slice(0, 5);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('he-IL');
  };

  const stats = getStats();
  const recentLeads = getRecentLeads();

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
      <div className="container mx-auto p-3 sm:p-6">
        <div className="mb-6 sm:mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold mb-2">ניהול לקוחות ולידים</h1>
          <p className="text-muted-foreground text-sm sm:text-base">
            ניהול לקוחות, מעקב לידים ושליחת דוחות ממותגים
          </p>
        </div>

        {/* Navigation Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 mb-6 sm:mb-8">
          <Link href="/crm/contacts">
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 rtl:flex-row-reverse">
                <CardTitle className="text-sm font-medium rtl:text-right">לקוחות</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent className="rtl:text-right">
                <div className="text-xl sm:text-2xl font-bold">{contacts.length}</div>
                <p className="text-xs text-muted-foreground">
                  לקוחות רשומים
                </p>
              </CardContent>
            </Card>
          </Link>

          <Link href="/crm/leads">
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 rtl:flex-row-reverse">
                <CardTitle className="text-sm font-medium rtl:text-right">לידים</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent className="rtl:text-right">
                <div className="text-xl sm:text-2xl font-bold">{stats.totalLeads}</div>
                <p className="text-xs text-muted-foreground">
                  {stats.newLeads} חדשים
                </p>
              </CardContent>
            </Card>
          </Link>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 rtl:flex-row-reverse">
              <CardTitle className="text-sm font-medium rtl:text-right">המרה</CardTitle>
              <CheckCircle className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent className="rtl:text-right">
              <div className="text-xl sm:text-2xl font-bold text-green-600">{stats.conversionRate}%</div>
              <p className="text-xs text-muted-foreground">
                {stats.closedWon} נסגרו בהצלחה
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-6 sm:mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 rtl:flex-row-reverse">
              <CardTitle className="text-sm font-medium rtl:text-right">סה״כ לידים</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent className="rtl:text-right">
              <div className="text-xl sm:text-2xl font-bold">{stats.totalLeads}</div>
              <p className="text-xs text-muted-foreground">
                {stats.newLeads} חדשים
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 rtl:flex-row-reverse">
              <CardTitle className="text-sm font-medium rtl:text-right">לידים פעילים</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent className="rtl:text-right">
              <div className="text-xl sm:text-2xl font-bold">{stats.activeLeads}</div>
              <p className="text-xs text-muted-foreground">
                במעקב פעיל
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 rtl:flex-row-reverse">
              <CardTitle className="text-sm font-medium rtl:text-right">נסגרו בהצלחה</CardTitle>
              <CheckCircle className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent className="rtl:text-right">
              <div className="text-xl sm:text-2xl font-bold text-green-600">{stats.closedWon}</div>
              <p className="text-xs text-muted-foreground">
                {stats.conversionRate}% המרה
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 rtl:flex-row-reverse">
              <CardTitle className="text-sm font-medium rtl:text-right">נסגרו ללא הצלחה</CardTitle>
              <XCircle className="h-4 w-4 text-red-600" />
            </CardHeader>
            <CardContent className="rtl:text-right">
              <div className="text-xl sm:text-2xl font-bold text-red-600">{stats.closedLost}</div>
              <p className="text-xs text-muted-foreground">
                לא התממשו
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 mb-6 sm:mb-8">
          <Card>
            <CardHeader className="rtl:text-right">
              <CardTitle className="text-base sm:text-lg">פעולות מהירות</CardTitle>
              <CardDescription className="text-sm">
                גישה מהירה לפעולות נפוצות
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-col sm:flex-row gap-2 rtl:flex-row-reverse">
                <Link href="/crm/contacts" className="flex-1">
                  <Button className="w-full" size="sm">
                    <Users className="h-4 w-4 ml-2 rtl:mr-2 rtl:ml-0" />
                    ניהול לקוחות
                  </Button>
                </Link>
                <Link href="/crm/leads" className="flex-1">
                  <Button variant="outline" className="w-full" size="sm">
                    <TrendingUp className="h-4 w-4 ml-2 rtl:mr-2 rtl:ml-0" />
                    ניהול לידים
                  </Button>
                </Link>
              </div>
              <div className="text-xs sm:text-sm text-muted-foreground rtl:text-right">
                כדי ליצור ליד חדש, עבור לעמוד נכסים ולחץ על &quot;שייך לקוח&quot;
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="rtl:text-right">
              <CardTitle className="text-base sm:text-lg">לידים אחרונים</CardTitle>
              <CardDescription className="text-sm">
                פעילות אחרונה במערכת
              </CardDescription>
            </CardHeader>
            <CardContent>
              {recentLeads.length === 0 ? (
                <div className="text-center py-4 text-muted-foreground rtl:text-right">
                  אין לידים עדיין
                </div>
              ) : (
                <div className="space-y-3">
                  {recentLeads.map((lead) => (
                    <div key={lead.id} className="flex items-center justify-between p-2 sm:p-3 bg-gray-50 rounded-lg rtl:flex-row-reverse">
                      <div className="flex-1 rtl:text-right min-w-0">
                        <div className="font-medium text-sm sm:text-base truncate">{lead.contact.name}</div>
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

        {/* Status Distribution */}
        {stats.totalLeads > 0 && (
          <Card>
            <CardHeader className="rtl:text-right">
              <CardTitle className="text-base sm:text-lg">התפלגות סטטוסים</CardTitle>
              <CardDescription className="text-sm">
                פילוח הלידים לפי סטטוס
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
                <div className="text-center">
                  <div className="text-lg sm:text-2xl font-bold text-blue-600">{stats.newLeads}</div>
                  <div className="text-xs sm:text-sm text-muted-foreground">חדשים</div>
                </div>
                <div className="text-center">
                  <div className="text-lg sm:text-2xl font-bold text-yellow-600">
                    {leads.filter(l => l.status === 'contacted').length}
                  </div>
                  <div className="text-xs sm:text-sm text-muted-foreground">יצרתי קשר</div>
                </div>
                <div className="text-center">
                  <div className="text-lg sm:text-2xl font-bold text-orange-600">
                    {leads.filter(l => l.status === 'interested').length}
                  </div>
                  <div className="text-xs sm:text-sm text-muted-foreground">מתעניינים</div>
                </div>
                <div className="text-center">
                  <div className="text-lg sm:text-2xl font-bold text-purple-600">
                    {leads.filter(l => l.status === 'negotiating').length}
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