'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/Badge';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogTrigger 
} from '@/components/ui/dialog';
import { Users, Plus, ExternalLink, MessageSquare } from 'lucide-react';
import { Lead, CrmApi } from '@/lib/api/crm';
import { LeadStatusBadge } from './lead-status-badge';
import { LeadRowActions } from './lead-row-actions';
import { AssignContactModal } from './assign-contact-modal';
import { useToast } from '@/hooks/use-toast';

interface AssetLeadsPanelProps {
  assetId: number;
  assetAddress?: string;
}

export function AssetLeadsPanel({ assetId, assetAddress }: AssetLeadsPanelProps) {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const { toast } = useToast();

  const loadLeads = useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await CrmApi.getLeadsByAsset(assetId);
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
  }, [assetId, toast]);

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

  const handleContactAssigned = () => {
    loadLeads();
    setIsAssignModalOpen(false);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('he-IL');
  };

  const getStatusCounts = () => {
    const counts = {
      new: 0,
      contacted: 0,
      interested: 0,
      negotiating: 0,
      'closed-won': 0,
      'closed-lost': 0,
    };

    leads.forEach(lead => {
      counts[lead.status]++;
    });

    return counts;
  };

  const statusCounts = getStatusCounts();

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between rtl:flex-row-reverse">
          <div className="rtl:text-right">
            <CardTitle className="flex items-center gap-2 rtl:flex-row-reverse">
              <Users className="h-5 w-5" />
              לקוחות משויכים
            </CardTitle>
            <CardDescription>
              ניהול לידים עבור נכס זה
            </CardDescription>
          </div>
          <AssignContactModal
            assetId={assetId}
            assetAddress={assetAddress}
            onCreated={handleContactAssigned}
            trigger={
              <Button size="sm">
                <Plus className="h-4 w-4 ml-2 rtl:mr-2 rtl:ml-0" />
                שייך לקוח
              </Button>
            }
          />
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="text-muted-foreground">טוען לידים...</div>
          </div>
        ) : leads.length === 0 ? (
          <div className="text-center py-8 rtl:text-right">
            <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <div className="text-lg font-medium mb-2">אין לקוחות משויכים</div>
            <div className="text-sm text-muted-foreground mb-4">
              התחל על ידי שיוך לקוח קיים או יצירת לקוח חדש
            </div>
            <AssignContactModal
              assetId={assetId}
              assetAddress={assetAddress}
              onCreated={handleContactAssigned}
              trigger={
                <Button>
                  <Plus className="h-4 w-4 ml-2 rtl:mr-2 rtl:ml-0" />
                  שייך לקוח ראשון
                </Button>
              }
            />
          </div>
        ) : (
          <div className="space-y-4">
            {/* Status Summary */}
            <div className="flex flex-wrap gap-2">
              {Object.entries(statusCounts).map(([status, count]) => {
                if (count === 0) return null;
                return (
                  <Badge key={status} variant="outline" className="flex items-center gap-1">
                    <span className="font-medium">{count}</span>
                    <span>
                      {status === 'new' && 'חדשים'}
                      {status === 'contacted' && 'יצרתי קשר'}
                      {status === 'interested' && 'מתעניינים'}
                      {status === 'negotiating' && 'במשא ומתן'}
                      {status === 'closed-won' && 'נסגרו בהצלחה'}
                      {status === 'closed-lost' && 'נסגרו ללא הצלחה'}
                    </span>
                  </Badge>
                );
              })}
            </div>

            {/* Leads Table */}
            <div className="border rounded-lg">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-right">לקוח</TableHead>
                    <TableHead className="text-right">סטטוס</TableHead>
                    <TableHead className="text-right">פעילות אחרונה</TableHead>
                    <TableHead className="text-right">פעולות</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {leads.map((lead) => (
                    <TableRow key={lead.id}>
                      <TableCell className="text-right">
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
                      <TableCell className="text-right">
                        <LeadStatusBadge status={lead.status} />
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="text-sm">
                          {formatDate(lead.last_activity_at)}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <LeadRowActions
                          lead={lead}
                          onUpdate={handleLeadUpdate}
                          onDelete={() => handleLeadDelete(lead)}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            {/* Recent Notes */}
            {leads.some(lead => lead.notes.length > 0) && (
              <div>
                <h4 className="font-medium mb-2 flex items-center gap-2 rtl:flex-row-reverse rtl:text-right">
                  <MessageSquare className="h-4 w-4" />
                  הערות אחרונות
                </h4>
                <div className="space-y-2">
                  {leads
                    .filter(lead => lead.notes.length > 0)
                    .slice(0, 3)
                    .map((lead) => (
                      <div key={lead.id} className="bg-gray-50 p-3 rounded-lg">
                        <div className="flex justify-between items-start mb-1 rtl:flex-row-reverse">
                          <div className="font-medium text-sm">{lead.contact.name}</div>
                          <LeadStatusBadge status={lead.status} />
                        </div>
                        <div className="space-y-1">
                          {lead.notes.slice(-1).map((note, index) => (
                            <div key={index} className="text-sm bg-white p-2 rounded border-l-2 rtl:border-r-2 rtl:border-l-0 border-blue-200 rtl:text-right">
                              <div className="text-xs text-muted-foreground mb-1">
                                {formatDate(note.ts)}
                              </div>
                              <div>{note.text}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
