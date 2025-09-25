'use client';

import { useState, useEffect, useCallback } from 'react';
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
import { Search, ExternalLink, Plus } from 'lucide-react';
import { Lead, CrmApi } from '@/lib/api/crm';
import { LeadStatusBadge } from '@/components/crm/lead-status-badge';
import { LeadRowActions } from '@/components/crm/lead-row-actions';
import { LeadTasksPanel } from '@/components/crm/lead-tasks-panel';
import { LeadTaskSummary } from '@/components/crm/lead-task-summary';
import { useToast } from '@/hooks/use-toast';
import DashboardLayout from '@/components/layout/dashboard-layout';
import { PageLoader } from '@/components/ui/page-loader';
import { Skeleton } from '@/components/ui/skeleton';
import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from '@/components/ui/breadcrumb';
import Link from 'next/link';

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLeadForTasks, setSelectedLeadForTasks] = useState<Lead | null>(null);
  const { toast } = useToast();

  const loadLeads = useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await CrmApi.getLeads();
      setLeads(data);
    } catch (error) {
      toast({
        title: 'שגיאה',
        description: 'לא ניתן לטעון את רשימת הלידים',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    loadLeads();
  }, [loadLeads]);

  const handleLeadUpdate = () => {
    loadLeads();
  };

  const handleLeadDelete = async (lead: Lead) => {
    if (!confirm(`האם אתה בטוח שברצונך למחוק את הליד של ${lead.contact.name}?`)) {
      return;
    }

    try {
      await CrmApi.deleteLead(lead.id);
      await loadLeads();
      toast({
        title: 'ליד נמחק',
        description: 'הליד נמחק בהצלחה',
      });
    } catch (error) {
      toast({
        title: 'שגיאה',
        description: 'לא ניתן למחוק את הליד',
        variant: 'destructive',
      });
    }
  };

  const handleShowTasks = (lead: Lead) => {
    setSelectedLeadForTasks(lead);
  };

  const filteredLeads = leads.filter(lead =>
    lead.contact.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    lead.contact.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    lead.asset_address.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatPrice = (price: number | null) => {
    if (!price) return '-';
    return new Intl.NumberFormat('he-IL').format(price) + ' ₪';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('he-IL');
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <PageLoader message="טוען לידים..." showLogo={false} />
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="container mx-auto p-6">
        <Breadcrumb className="mb-6">
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink href="/crm">לקוחות ולידים</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbPage>לידים</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
        
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold">לידים</h1>
          <Link href="/assets">
            <Button>
              <Plus className="h-4 w-4 ml-2" />
              צור ליד חדש
            </Button>
          </Link>
        </div>

      <div className="mb-6">
        <div className="relative">
          <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <Input
            placeholder="חפש לידים..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pr-10"
          />
        </div>
      </div>

      {filteredLeads.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-lg text-muted-foreground mb-4">
            {searchQuery ? 'לא נמצאו לידים התואמים לחיפוש' : 'אין עדיין לידים'}
          </div>
          <div className="text-sm text-muted-foreground mb-4">
            כדי ליצור ליד, עבור לעמוד נכס ולחץ על &quot;שייך לקוח&quot;
          </div>
          {!searchQuery && (
            <Link href="/assets">
              <Button>
                <Plus className="h-4 w-4 ml-2" />
                עבור לנכסים ליצירת ליד
              </Button>
            </Link>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>לקוח</TableHead>
                <TableHead>נכס</TableHead>
                <TableHead>משימות</TableHead>
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
                    <div className="flex items-center gap-2">
                      <div>
                        <div className="font-medium">{lead.asset_address}</div>
                        <Button
                          variant="link"
                          size="sm"
                          className="p-0 h-auto"
                          onClick={() => window.open(`/assets/${lead.asset_id_read}`, '_blank')}
                        >
                          <ExternalLink className="h-3 w-3 mr-1" />
                          צפה בנכס
                        </Button>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <LeadTaskSummary 
                      lead={lead} 
                      onShowTasks={() => handleShowTasks(lead)}
                      compact={false}
                    />
                  </TableCell>
                  <TableCell>
                    <LeadStatusBadge status={lead.status} />
                  </TableCell>
                  <TableCell>
                    <div className="text-sm">
                      {formatDate(lead.last_activity_at)}
                    </div>
                  </TableCell>
                  <TableCell>
                    <LeadRowActions
                      lead={lead}
                      onUpdate={handleLeadUpdate}
                      onDelete={() => handleLeadDelete(lead)}
                      onShowTasks={() => handleShowTasks(lead)}
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}


      {/* Tasks Panel */}
      {selectedLeadForTasks && (
        <LeadTasksPanel
          lead={selectedLeadForTasks}
          onClose={() => setSelectedLeadForTasks(null)}
        />
      )}
      </div>
    </DashboardLayout>
  );
}
