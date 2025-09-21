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
  Plus, 
  Search, 
  Edit, 
  Trash2
} from 'lucide-react';
import { Lead, Contact, CrmApi, CreateContactData } from '@/lib/api/crm';
import Link from 'next/link';
import DashboardLayout from '@/components/layout/dashboard-layout';
import { useToast } from '@/hooks/use-toast';
import { PageLoader } from '@/components/ui/page-loader';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table';
import { Badge } from '@/components/ui/Badge';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogTrigger 
} from '@/components/ui/dialog';
import { ContactForm } from '@/components/crm/contact-form';
import { LeadStatusBadge } from '@/components/crm/lead-status-badge';
import { LeadRowActions } from '@/components/crm/lead-row-actions';

export default function CrmPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [searchQuery, setSearchQuery] = useState('');
  const [isCreateContactDialogOpen, setIsCreateContactDialogOpen] = useState(false);
  const [editingContact, setEditingContact] = useState<Contact | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();

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
    loadAllData();
  }, [loadAllData]);

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

  const formatEquity = (value: number | null) => {
    if (value === null || Number.isNaN(value)) {
      return '-';
    }

    return new Intl.NumberFormat('he-IL', {
      style: 'currency',
      currency: 'ILS',
      maximumFractionDigits: 0
    }).format(value);
  };

  // Contact handlers
  const handleCreateContact = async (data: CreateContactData) => {
    try {
      setIsSubmitting(true);
      await CrmApi.createContact(data);
      toast({
        title: 'לקוח נוצר',
        description: 'הלקוח החדש נוצר בהצלחה.',
      });
      setIsCreateContactDialogOpen(false);
      loadContacts();
    } catch (error: any) {
      toast({
        title: 'שגיאה',
        description: error.message || 'לא ניתן ליצור לקוח חדש.',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateContact = async (data: Partial<CreateContactData>) => {
    if (!editingContact) return;
    try {
      setIsSubmitting(true);
      await CrmApi.updateContact(editingContact.id, data);
      toast({
        title: 'לקוח עודכן',
        description: 'פרטי הלקוח עודכנו בהצלחה.',
      });
      setEditingContact(null);
      loadContacts();
    } catch (error: any) {
      toast({
        title: 'שגיאה',
        description: error.message || 'לא ניתן לעדכן את פרטי הלקוח.',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteContact = async (id: number) => {
    if (!confirm('האם אתה בטוח שברצונך למחוק לקוח זה?')) return;
    try {
      await CrmApi.deleteContact(id);
      toast({
        title: 'לקוח נמחק',
        description: 'הלקוח נמחק בהצלחה.',
      });
      loadContacts();
    } catch (error: any) {
      toast({
        title: 'שגיאה',
        description: error.message || 'לא ניתן למחוק את הלקוח.',
        variant: 'destructive',
      });
    }
  };

  const handleLeadUpdate = () => {
    loadLeads();
  };

  const handleLeadDelete = () => {
    loadLeads();
  };

  // Filter functions
  const filteredContacts = contacts.filter(contact => {
    const normalizedQuery = searchQuery.toLowerCase();
    const equityQuery = contact.equity !== null ? contact.equity.toString() : '';

    return (
      contact.name.toLowerCase().includes(normalizedQuery) ||
      (contact.email || '').toLowerCase().includes(normalizedQuery) ||
      (contact.phone || '').includes(searchQuery) ||
      contact.tags.some(tag => tag.toLowerCase().includes(normalizedQuery)) ||
      equityQuery.includes(searchQuery)
    );
  });

  const filteredLeads = leads.filter(lead =>
    lead.contact.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    lead.asset_address?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    lead.status.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const stats = getStats();
  const recentLeads = getRecentLeads();

  if (isLoading) {
    return (
      <DashboardLayout>
        <PageLoader message="טוען נתוני CRM..." showLogo={false} />
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="container mx-auto p-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">ניהול לקוחות ולידים</h1>
          <p className="text-muted-foreground">
            ניהול לקוחות, מעקב לידים ושליחת דוחות ממותגים
          </p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="leads">לידים</TabsTrigger>
            <TabsTrigger value="contacts">לקוחות</TabsTrigger>
            <TabsTrigger value="dashboard">כללי</TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard" className="space-y-6">
            {/* Stats Cards */}
            <div className="flex flex-col md:flex-row lg:flex-row gap-6 mb-8 rtl:flex-row-reverse">
        <Card className="flex-1">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 rtl:flex-row-reverse">
            <CardTitle className="text-sm font-medium rtl:text-right">סה״כ לידים</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent className="rtl:text-right">
            <div className="text-2xl font-bold">{stats.totalLeads}</div>
            <p className="text-xs text-muted-foreground">
              {stats.newLeads} חדשים
            </p>
          </CardContent>
        </Card>

        <Card className="flex-1">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 rtl:flex-row-reverse">
            <CardTitle className="text-sm font-medium rtl:text-right">לידים פעילים</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent className="rtl:text-right">
            <div className="text-2xl font-bold">{stats.activeLeads}</div>
            <p className="text-xs text-muted-foreground">
              במעקב פעיל
            </p>
          </CardContent>
        </Card>

        <Card className="flex-1">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 rtl:flex-row-reverse">
            <CardTitle className="text-sm font-medium rtl:text-right">נסגרו בהצלחה</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent className="rtl:text-right">
            <div className="text-2xl font-bold text-green-600">{stats.closedWon}</div>
            <p className="text-xs text-muted-foreground">
              {stats.conversionRate}% המרה
            </p>
          </CardContent>
        </Card>

        <Card className="flex-1">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 rtl:flex-row-reverse">
            <CardTitle className="text-sm font-medium rtl:text-right">נסגרו ללא הצלחה</CardTitle>
            <XCircle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent className="rtl:text-right">
            <div className="text-2xl font-bold text-red-600">{stats.closedLost}</div>
            <p className="text-xs text-muted-foreground">
              לא התממשו
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Card className="flex-1">
          <CardHeader className="rtl:text-right">
            <CardTitle>פעולות מהירות</CardTitle>
            <CardDescription>
              גישה מהירה לפעולות נפוצות
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2 rtl:flex-row-reverse">
              <Button 
                className="flex-1"
                onClick={() => setActiveTab('contacts')}
              >
                <Users className="h-4 w-4 ml-2 rtl:mr-2 rtl:ml-0" />
                ניהול לקוחות
              </Button>
              <Button 
                variant="outline" 
                className="flex-1"
                onClick={() => setActiveTab('leads')}
              >
                <TrendingUp className="h-4 w-4 ml-2 rtl:mr-2 rtl:ml-0" />
                ניהול לידים
              </Button>
            </div>
            <div className="text-sm text-muted-foreground rtl:text-right">
              כדי ליצור ליד חדש, עבור לעמוד נכס ולחץ על &quot;שייך לקוח&quot;
            </div>
          </CardContent>
        </Card>

        <Card className="flex-1">
          <CardHeader className="rtl:text-right">
            <CardTitle>לידים אחרונים</CardTitle>
            <CardDescription>
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
                  <div key={lead.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg rtl:flex-row-reverse">
                    <div className="flex-1 rtl:text-right">
                      <div className="font-medium">{lead.contact.name}</div>
                      <div className="text-sm text-muted-foreground">
                        {lead.asset_address}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 rtl:flex-row-reverse">
                      <Badge variant="outline">
                        {lead.status === 'new' && 'חדש'}
                        {lead.status === 'contacted' && 'יצרתי קשר'}
                        {lead.status === 'interested' && 'מתעניין'}
                        {lead.status === 'negotiating' && 'במשא ומתן'}
                        {lead.status === 'closed-won' && 'נסגר בהצלחה'}
                        {lead.status === 'closed-lost' && 'נסגר ללא הצלחה'}
                      </Badge>
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => setActiveTab('leads')}
                      >
                        <ArrowRight className="h-4 w-4" />
                      </Button>
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
        <Card className="flex-1">
          <CardHeader className="rtl:text-right">
            <CardTitle>התפלגות סטטוסים</CardTitle>
            <CardDescription>
              פילוח הלידים לפי סטטוס
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{stats.newLeads}</div>
                <div className="text-sm text-muted-foreground">חדשים</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">
                  {leads.filter(l => l.status === 'contacted').length}
                </div>
                <div className="text-sm text-muted-foreground">יצרתי קשר</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {leads.filter(l => l.status === 'interested').length}
                </div>
                <div className="text-sm text-muted-foreground">מתעניינים</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {leads.filter(l => l.status === 'negotiating').length}
                </div>
                <div className="text-sm text-muted-foreground">במשא ומתן</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{stats.closedWon}</div>
                <div className="text-sm text-muted-foreground">נסגרו בהצלחה</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{stats.closedLost}</div>
                <div className="text-sm text-muted-foreground">נסגרו ללא הצלחה</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
          </TabsContent>

          <TabsContent value="contacts" className="space-y-6">
            <div className="flex justify-between items-center rtl:flex-row-reverse">
              <h2 className="text-2xl font-bold rtl:text-right">לקוחות</h2>
              <Dialog open={isCreateContactDialogOpen} onOpenChange={setIsCreateContactDialogOpen}>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="mr-2 rtl:ml-2 rtl:mr-0 h-4 w-4" /> לקוח חדש
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>צור לקוח חדש</DialogTitle>
                  </DialogHeader>
                  <ContactForm onSubmit={handleCreateContact} isLoading={isSubmitting} />
                </DialogContent>
              </Dialog>
            </div>

            <div className="relative">
              <Search className="absolute right-2 rtl:left-2 rtl:right-auto top-3 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="חפש לקוח (שם, אימייל, טלפון, תגית)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pr-8 rtl:pl-8 rtl:pr-0"
              />
            </div>

            {filteredContacts.length === 0 ? (
              <div className="text-center py-12 rtl:text-right">
                <div className="text-lg text-muted-foreground mb-4">
                  {searchQuery ? 'לא נמצאו לקוחות התואמים לחיפוש' : 'אין עדיין לקוחות'}
                </div>
                {!searchQuery && (
                  <Button onClick={() => setIsCreateContactDialogOpen(true)}>
                    <Plus className="h-4 w-4 ml-2 rtl:mr-2 rtl:ml-0" />
                    צור לקוח ראשון
                  </Button>
                )}
              </div>
            ) : (
              <div className="bg-white rounded-lg border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-right">שם</TableHead>
                      <TableHead className="text-right">אימייל</TableHead>
                      <TableHead className="text-right">טלפון</TableHead>
                      <TableHead className="text-right">הון עצמי</TableHead>
                      <TableHead className="text-right">תגיות</TableHead>
                      <TableHead className="text-right">נוצר</TableHead>
                      <TableHead className="text-right">פעולות</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredContacts.map((contact) => (
                      <TableRow key={contact.id}>
                        <TableCell className="font-medium text-right">{contact.name}</TableCell>
                        <TableCell className="text-right">{contact.email || '-'}</TableCell>
                        <TableCell className="text-right">{contact.phone || '-'}</TableCell>
                        <TableCell className="text-right">{formatEquity(contact.equity)}</TableCell>
                        <TableCell className="text-right">
                          <div className="flex flex-wrap gap-1 rtl:flex-row-reverse">
                            {contact.tags.map((tag) => (
                              <Badge key={tag} variant="secondary" className="text-xs">
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        </TableCell>
                        <TableCell className="text-right">{formatDate(contact.created_at)}</TableCell>
                        <TableCell className="text-right">
                          <div className="flex gap-2 rtl:flex-row-reverse">
                            <Button 
                              variant="outline" 
                              size="sm" 
                              onClick={() => setEditingContact(contact)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button 
                              variant="outline" 
                              size="sm" 
                              onClick={() => handleDeleteContact(contact.id)}
                              className="text-destructive hover:text-destructive"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </TabsContent>

          <TabsContent value="leads" className="space-y-6">
            <div className="flex justify-between items-center rtl:flex-row-reverse">
              <h2 className="text-2xl font-bold rtl:text-right">לידים</h2>
            </div>

            <div className="relative">
              <Search className="absolute right-2 rtl:left-2 rtl:right-auto top-3 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="חפש ליד (לקוח, נכס, סטטוס)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pr-8 rtl:pl-8 rtl:pr-0"
              />
            </div>

            {filteredLeads.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-lg text-muted-foreground mb-4">
                  {searchQuery ? 'לא נמצאו לידים התואמים לחיפוש' : 'אין עדיין לידים'}
                </div>
                <div className="text-sm text-muted-foreground">
                  כדי ליצור ליד, עבור לעמוד נכס ולחץ על &quot;שייך לקוח&quot;
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>לקוח</TableHead>
                      <TableHead>נכס</TableHead>
                      <TableHead>סטטוס</TableHead>
                      <TableHead>פעילות אחרונה</TableHead>
                      <TableHead className="text-left">פעולות</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredLeads.map((lead) => (
                      <TableRow key={lead.id}>
                        <TableCell>
                          <div>
                            <div className="font-medium">{lead.contact.name}</div>
                            {lead.contact.email && (
                              <div className="text-sm text-muted-foreground">
                                {lead.contact.email}
                              </div>
                            )}
                            {lead.contact.phone && (
                              <div className="text-sm text-muted-foreground">
                                {lead.contact.phone}
                              </div>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Link href={`/assets/${lead.asset_id}`} className="text-blue-600 hover:underline">
                            {lead.asset_address}
                          </Link>
                        </TableCell>
                        <TableCell>
                          <LeadStatusBadge status={lead.status} />
                        </TableCell>
                        <TableCell>{formatDate(lead.last_activity_at)}</TableCell>
                        <TableCell className="text-left">
                          <LeadRowActions 
                            lead={lead} 
                            onUpdate={handleLeadUpdate} 
                            onDelete={handleLeadDelete} 
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </TabsContent>
        </Tabs>

        {/* Edit Contact Dialog */}
        {editingContact && (
          <Dialog open={!!editingContact} onOpenChange={() => setEditingContact(null)}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>ערוך לקוח</DialogTitle>
              </DialogHeader>
              <ContactForm 
                initialData={editingContact} 
                onSubmit={handleUpdateContact} 
                onCancel={() => setEditingContact(null)}
                isLoading={isSubmitting}
              />
            </DialogContent>
          </Dialog>
        )}
      </div>
    </DashboardLayout>
  );
}
