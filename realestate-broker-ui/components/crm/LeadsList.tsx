'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/Badge';
import {
  Search,
  ExternalLink,
  Plus,
  ChevronDown,
  ChevronRight,
  Edit,
  Trash2,
} from 'lucide-react';
import {
  Lead,
  CrmApi,
  ContactTask,
  CreateTaskData,
  UpdateTaskData,
} from '@/lib/api/crm';
import { LeadStatusBadge } from '@/components/crm/lead-status-badge';
import { LeadRowActions } from '@/components/crm/lead-row-actions';
import { LeadTaskSummary, clearTaskCache } from '@/components/crm/lead-task-summary';
import { TaskForm } from '@/components/crm/task-form';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { useToast } from '@/hooks/use-toast';
import { PageLoader } from '@/components/ui/page-loader';

export type CommonListProps = {
  initialQuery?: string;
  initialFilters?: Record<string, string | string[] | undefined>;
  onConvertedToClient?: (contactId: number) => void;
};

type LeadsListProps = CommonListProps;

export default function LeadsList({
  initialQuery = '',
  initialFilters, // Reserved for future filtering enhancements
  onConvertedToClient,
}: LeadsListProps) {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState(initialQuery);
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
  const [leadTasks, setLeadTasks] = useState<Map<number, ContactTask[]>>(new Map());
  const [isCreateTaskModalOpen, setIsCreateTaskModalOpen] = useState<number | null>(null);
  const [editingTask, setEditingTask] = useState<ContactTask | null>(null);
  const { toast } = useToast();

  // The conversion callback is reserved for future use when inline conversion is added
  void onConvertedToClient;
  void initialFilters;

  useEffect(() => {
    setSearchQuery(initialQuery);
  }, [initialQuery]);

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

  const toggleRowExpansion = (leadId: number) => {
    setExpandedRows((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(leadId)) {
        newSet.delete(leadId);
      } else {
        newSet.add(leadId);
        loadTasksForLead(leadId);
      }
      return newSet;
    });
  };

  const loadTasksForLead = async (leadId: number) => {
    try {
      const tasks = await CrmApi.getLeadTasks(leadId);
      setLeadTasks((prev) => new Map(prev.set(leadId, tasks)));
    } catch (error) {
      toast({
        title: 'שגיאה',
        description: 'לא ניתן לטעון את המשימות',
        variant: 'destructive',
      });
    }
  };

  const handleCreateTask = async (leadId: number, data: CreateTaskData | UpdateTaskData) => {
    try {
      const createData: CreateTaskData = {
        title: data.title || '',
        description: data.description,
        due_at: data.due_at,
        contact_id: leads.find((l) => l.id === leadId)?.contact_id || 0,
        lead_id_write: leadId,
        status: data.status || 'pending',
      };

      await CrmApi.createTask(createData);
      await loadTasksForLead(leadId);
      clearTaskCache(leadId);
      setIsCreateTaskModalOpen(null);
      toast({
        title: 'משימה נוצרה',
        description: 'המשימה נוצרה בהצלחה',
      });
    } catch (error) {
      toast({
        title: 'שגיאה',
        description: 'לא ניתן ליצור את המשימה',
        variant: 'destructive',
      });
    }
  };

  const handleCompleteTask = async (leadId: number, taskId: number) => {
    try {
      await CrmApi.completeTask(taskId);
      await loadTasksForLead(leadId);
      clearTaskCache(leadId);
      toast({
        title: 'משימה הושלמה',
        description: 'המשימה סומנה כהושלמה',
      });
    } catch (error) {
      toast({
        title: 'שגיאה',
        description: 'לא ניתן להשלים את המשימה',
        variant: 'destructive',
      });
    }
  };

  const handleEditTask = async (leadId: number, data: CreateTaskData | UpdateTaskData) => {
    if (!editingTask) return;

    try {
      const updateData: UpdateTaskData = {
        title: data.title || editingTask.title,
        description: data.description || editingTask.description,
        due_at: data.due_at || editingTask.due_at || undefined,
        status: data.status || editingTask.status,
      };

      await CrmApi.updateTask(editingTask.id, updateData);
      await loadTasksForLead(leadId);
      clearTaskCache(leadId);
      setEditingTask(null);
      toast({
        title: 'משימה עודכנה',
        description: 'המשימה עודכנה בהצלחה',
      });
    } catch (error) {
      toast({
        title: 'שגיאה',
        description: 'לא ניתן לעדכן את המשימה',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteTask = async (leadId: number, taskId: number) => {
    if (!confirm('האם אתה בטוח שברצונך למחוק את המשימה?')) {
      return;
    }

    try {
      await CrmApi.deleteTask(taskId);
      await loadTasksForLead(leadId);
      clearTaskCache(leadId);
      toast({
        title: 'משימה נמחקה',
        description: 'המשימה נמחקה בהצלחה',
      });
    } catch (error) {
      toast({
        title: 'שגיאה',
        description: 'לא ניתן למחוק את המשימה',
        variant: 'destructive',
      });
    }
  };

  const filteredLeads = useMemo(
    () =>
      leads.filter(
        (lead) =>
          lead.contact.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          lead.contact.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
          lead.asset_address.toLowerCase().includes(searchQuery.toLowerCase())
      ),
    [leads, searchQuery]
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
      <div className="flex justify-center py-10">
        <PageLoader message="טוען לידים..." showLogo={false} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between rtl:flex-row-reverse">
        <h2 className="text-2xl font-bold rtl:text-right">לידים</h2>
        <Link href="/assets">
          <Button>
            <Plus className="h-4 w-4 ml-2 rtl:mr-2 rtl:ml-0" />
            צור ליד חדש
          </Button>
        </Link>
      </div>

      <div className="mb-2">
        <div className="relative">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 h-4 w-4" />
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
        <div className="bg-white rounded-lg border overflow-x-auto">
          <div className="min-w-full">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-8 whitespace-nowrap"></TableHead>
                  <TableHead className="whitespace-nowrap min-w-[150px] rtl:text-right">לקוח</TableHead>
                  <TableHead className="whitespace-nowrap min-w-[150px] rtl:text-right">נכס</TableHead>
                  <TableHead className="whitespace-nowrap min-w-[100px] rtl:text-right">משימות</TableHead>
                  <TableHead className="whitespace-nowrap min-w-[100px] rtl:text-right">סטטוס</TableHead>
                  <TableHead className="whitespace-nowrap min-w-[120px] rtl:text-right">פעילות אחרונה</TableHead>
                  <TableHead className="rtl:text-right whitespace-nowrap min-w-[120px]">פעולות</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredLeads.map((lead) => (
                  <React.Fragment key={lead.id}>
                    <TableRow>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => toggleRowExpansion(lead.id)}
                          className="h-8 w-8 p-0 min-h-[44px] min-w-[44px]"
                        >
                          {expandedRows.has(lead.id) ? (
                            <ChevronDown className="h-3 w-3" />
                          ) : (
                            <ChevronRight className="h-3 w-3" />
                          )}
                        </Button>
                      </TableCell>
                      <TableCell>
                        <div className="rtl:text-right">
                          <div className="font-medium">{lead.contact.name}</div>
                          {lead.contact.email && (
                            <div className="text-sm text-muted-foreground">{lead.contact.email}</div>
                          )}
                          {lead.contact.phone && (
                            <div className="text-sm text-muted-foreground">{lead.contact.phone}</div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2 rtl:flex-row-reverse">
                          <div className="rtl:text-right">
                            <div className="font-medium">{lead.asset_address}</div>
                            <Button
                              variant="link"
                              size="sm"
                              className="p-0 h-auto min-h-[44px]"
                              onClick={() => window.open(`/assets/${lead.asset_id_read}`, '_blank')}
                            >
                              <ExternalLink className="h-3 w-3 ml-1 rtl:mr-1 rtl:ml-0" />
                              צפה בנכס
                            </Button>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="rtl:text-right">
                          <LeadTaskSummary lead={lead} compact={true} />
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="rtl:text-right">
                          <LeadStatusBadge status={lead.status} />
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm rtl:text-right">{formatDate(lead.last_activity_at)}</div>
                      </TableCell>
                      <TableCell>
                        <LeadRowActions
                          lead={lead}
                          onUpdate={handleLeadUpdate}
                          onDelete={() => handleLeadDelete(lead)}
                        />
                      </TableCell>
                    </TableRow>

                    {expandedRows.has(lead.id) && (
                      <TableRow>
                        <TableCell colSpan={7} className="bg-gray-50 p-4">
                          <div className="space-y-4">
                            {lead.notes.length > 0 && (
                              <div>
                                <h4 className="font-medium mb-2">הערות</h4>
                                <div className="space-y-2">
                                  {lead.notes.map((note, index) => (
                                    <div key={index} className="bg-white p-3 rounded border-r-4 border-blue-200">
                                      <div className="text-xs text-muted-foreground mb-1">
                                        {formatDate(note.ts)}
                                      </div>
                                      <div className="text-sm">{note.text}</div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            <div>
                              <h4 className="font-medium mb-2">פרטי לקוח</h4>
                              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                                <div>
                                  <span className="text-muted-foreground">שם:</span> {lead.contact.name}
                                </div>
                                {lead.contact.email && (
                                  <div>
                                    <span className="text-muted-foreground">אימייל:</span> {lead.contact.email}
                                  </div>
                                )}
                                {lead.contact.phone && (
                                  <div>
                                    <span className="text-muted-foreground">טלפון:</span> {lead.contact.phone}
                                  </div>
                                )}
                                {lead.contact.equity && (
                                  <div>
                                    <span className="text-muted-foreground">הון עצמי:</span> {formatPrice(lead.contact.equity)}
                                  </div>
                                )}
                                {lead.contact.tags && lead.contact.tags.length > 0 && (
                                  <div className="sm:col-span-2">
                                    <span className="text-muted-foreground">תגיות:</span>
                                    <div className="flex flex-wrap gap-1 mt-1">
                                      {lead.contact.tags.map((tag, index) => (
                                        <Badge key={index} variant="secondary" className="text-xs">
                                          {tag}
                                        </Badge>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>

                            <div>
                              <h4 className="font-medium mb-2">פרטי נכס</h4>
                              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
                                <div>
                                  <span className="text-muted-foreground">כתובת:</span> {lead.asset_address}
                                </div>
                                <div>
                                  <span className="text-muted-foreground">מחיר:</span> {formatPrice(lead.asset_price)}
                                </div>
                                <div>
                                  <span className="text-muted-foreground">חדרים:</span> {lead.asset_rooms || '-'}
                                </div>
                                <div>
                                  <span className="text-muted-foreground">שטח:</span>{' '}
                                  {lead.asset_area ? `${lead.asset_area} מ״ר` : '-'}
                                </div>
                              </div>
                            </div>

                            <div>
                              <div className="flex items-center justify-between mb-3">
                                <h4 className="font-medium">ניהול משימות</h4>
                                <div className="flex items-center gap-2">
                                  <LeadTaskSummary lead={lead} compact={false} />
                                  <Dialog
                                    open={isCreateTaskModalOpen === lead.id}
                                    onOpenChange={(open) => setIsCreateTaskModalOpen(open ? lead.id : null)}
                                  >
                                    <DialogTrigger asChild>
                                      <Button size="sm" className="h-7 px-3">
                                        <Plus className="h-3 w-3 mr-1" />
                                        משימה חדשה
                                      </Button>
                                    </DialogTrigger>
                                    <DialogContent className="mx-4 sm:mx-0">
                                      <DialogHeader>
                                        <DialogTitle>יצירת משימה חדשה</DialogTitle>
                                      </DialogHeader>
                                      <TaskForm
                                        onSubmit={(data) => handleCreateTask(lead.id, data)}
                                        onCancel={() => setIsCreateTaskModalOpen(null)}
                                      />
                                    </DialogContent>
                                  </Dialog>
                                </div>

                                <Dialog open={!!editingTask} onOpenChange={(open) => !open && setEditingTask(null)}>
                                  <DialogContent className="mx-4 sm:mx-0">
                                    <DialogHeader>
                                      <DialogTitle>עריכת משימה</DialogTitle>
                                    </DialogHeader>
                                    <TaskForm
                                      initialData={
                                        editingTask
                                          ? {
                                              title: editingTask.title,
                                              description: editingTask.description,
                                              due_at: editingTask.due_at || undefined,
                                              status: editingTask.status,
                                            }
                                          : undefined
                                      }
                                      onSubmit={(data) => editingTask && handleEditTask(lead.id, data)}
                                      onCancel={() => setEditingTask(null)}
                                    />
                                  </DialogContent>
                                </Dialog>
                              </div>

                              <div className="space-y-2">
                                {leadTasks.get(lead.id)?.length === 0 ? (
                                  <div className="text-sm text-muted-foreground text-center py-4">
                                    אין משימות עדיין
                                  </div>
                                ) : (
                                  leadTasks.get(lead.id)?.map((task) => (
                                    <div
                                      key={task.id}
                                      className="flex items-center justify-between p-3 bg-white rounded border"
                                    >
                                      <div className="flex-1">
                                        <div className="font-medium text-sm">{task.title}</div>
                                        {task.description && (
                                          <div className="text-xs text-muted-foreground mt-1">{task.description}</div>
                                        )}
                                        {task.due_at && (
                                          <div className="text-xs text-muted-foreground mt-1">
                                            תאריך יעד: {formatDate(task.due_at)}
                                          </div>
                                        )}
                                      </div>
                                      <div className="flex items-center gap-2">
                                        <Badge
                                          variant={
                                            task.status === 'completed'
                                              ? 'default'
                                              : task.status === 'pending'
                                              ? 'secondary'
                                              : 'destructive'
                                          }
                                          className="text-xs"
                                        >
                                          {task.status === 'completed'
                                            ? 'הושלם'
                                            : task.status === 'pending'
                                            ? 'ממתין'
                                            : 'בוטל'}
                                        </Badge>
                                        <div className="flex items-center gap-1">
                                          {task.status === 'pending' && (
                                            <Button
                                              variant="outline"
                                              size="sm"
                                              onClick={() => handleCompleteTask(lead.id, task.id)}
                                              className="h-6 px-2 text-xs"
                                            >
                                              השלם
                                            </Button>
                                          )}
                                          <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => setEditingTask(task)}
                                            className="h-6 w-6 p-0"
                                            title="ערוך משימה"
                                          >
                                            <Edit className="h-3 w-3" />
                                          </Button>
                                          <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => handleDeleteTask(lead.id, task.id)}
                                            className="h-6 w-6 p-0 text-destructive hover:text-destructive"
                                            title="מחק משימה"
                                          >
                                            <Trash2 className="h-3 w-3" />
                                          </Button>
                                        </div>
                                      </div>
                                    </div>
                                  ))
                                )}
                              </div>
                            </div>
                          </div>
                        </TableCell>
                      </TableRow>
                    )}
                  </React.Fragment>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      )}
    </div>
  );
}
