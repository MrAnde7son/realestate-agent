'use client';

import React, { useMemo, useState, useCallback, useEffect } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/Badge';
import {
  Plus,
  Search,
  ChevronRight,
  ChevronDown,
  ExternalLink,
  Edit,
  Trash2,
  CheckSquare,
} from 'lucide-react';
import { Contact, ContactTask, CreateContactData, Lead } from '@/lib/api/crm';
import { CrmApi } from '@/lib/api/crm';
import { useToast } from '@/hooks/use-toast';
import { ContactForm } from '@/components/crm/contact-form';
import { LeadStatusBadge } from '@/components/crm/lead-status-badge';
import { LeadTaskSummary } from '@/components/crm/lead-task-summary';
import { LeadRowActions } from '@/components/crm/lead-row-actions';
import { ButtonLoader, PageLoader } from '@/components/ui/page-loader';
import { TaskForm } from '@/components/crm/task-form';

interface CombinedCrmTableProps {
  contacts: Contact[];
  leads: Lead[];
  onRefresh: () => Promise<void>;
}

type CombinedRow = {
  contact: Contact;
  leads: Lead[];
};

export function CombinedCrmTable({ contacts, leads, onRefresh }: CombinedCrmTableProps) {
  const { toast } = useToast();
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [editingContact, setEditingContact] = useState<Contact | null>(null);
  const [tasks, setTasks] = useState<ContactTask[]>([]);
  const [isTasksLoading, setIsTasksLoading] = useState(false);
  const [activeTaskContact, setActiveTaskContact] = useState<number | null>(null);
  const [isTaskDialogOpen, setIsTaskDialogOpen] = useState(false);

  const loadTasks = useCallback(async () => {
    try {
      setIsTasksLoading(true);
      const data = await CrmApi.getTasks();
      setTasks(data);
    } catch (error) {
      console.error('Failed to load tasks:', error);
      toast({
        title: 'שגיאה',
        description: 'לא ניתן לטעון את המשימות',
        variant: 'destructive',
      });
    } finally {
      setIsTasksLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    void loadTasks();
  }, [loadTasks]);

  const combinedRows = useMemo<CombinedRow[]>(() => {
    const leadsByContact = leads.reduce<Map<number, Lead[]>>((acc, lead) => {
      const existing = acc.get(lead.contact_id) || [];
      existing.push(lead);
      acc.set(lead.contact_id, existing);
      return acc;
    }, new Map());

    const rows = contacts.map((contact) => ({
      contact,
      leads: leadsByContact.get(contact.id) || [],
    }));

    rows.sort((a, b) => {
      const aLast = getLastActivity(a);
      const bLast = getLastActivity(b);
      return bLast.getTime() - aLast.getTime();
    });

    return rows;
  }, [contacts, leads]);

  const tasksByContact = useMemo(() => {
    return tasks.reduce<Map<number, ContactTask[]>>((acc, task) => {
      const current = acc.get(task.contact_id) || [];
      current.push(task);
      acc.set(task.contact_id, current);
      return acc;
    }, new Map());
  }, [tasks]);

  const toggleRowExpansion = (contactId: number) => {
    setExpandedRows((prev) => {
      const next = new Set(prev);
      if (next.has(contactId)) {
        next.delete(contactId);
      } else {
        next.add(contactId);
      }
      return next;
    });
  };

  const filteredRows = useMemo(() => {
    const query = searchQuery.toLowerCase().trim();
    if (!query) {
      return combinedRows;
    }

    return combinedRows.filter(({ contact, leads }) => {
      const matchesContact =
        contact.name.toLowerCase().includes(query) ||
        contact.email.toLowerCase().includes(query) ||
        contact.phone.toLowerCase().includes(query) ||
        contact.tags.some((tag) => tag.toLowerCase().includes(query));

      if (matchesContact) {
        return true;
      }

      return leads.some((lead) =>
        lead.asset_address.toLowerCase().includes(query)
      );
    });
  }, [combinedRows, searchQuery]);

  const handleCreateContact = async (data: CreateContactData & { selectedAsset?: any }) => {
    try {
      setIsSubmitting(true);
      const contact = await CrmApi.createContact(data);

      if (data.selectedAsset) {
        try {
          await CrmApi.createLead({
            contact_id_write: contact.id,
            asset_id: data.selectedAsset.id,
            status: 'new',
          });
        } catch (leadError) {
          console.error('Failed creating lead for new contact:', leadError);
          toast({
            title: 'לקוח נוצר, שגיאה בליד',
            description: 'הלקוח נוצר בהצלחה אך לא ניתן ליצור ליד עבור הנכס שנבחר.',
            variant: 'destructive',
          });
        }
      }

      toast({
        title: 'לקוח נוצר',
        description: 'הלקוח החדש נוצר בהצלחה',
      });

      setIsCreateDialogOpen(false);
      await onRefresh();
      await loadTasks();
    } catch (error: any) {
      toast({
        title: 'שגיאה',
        description: error.message || 'לא ניתן ליצור לקוח חדש',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateContact = async (data: CreateContactData & { selectedAsset?: any }) => {
    if (!editingContact) {
      return;
    }

    try {
      setIsSubmitting(true);
      await CrmApi.updateContact(editingContact.id, data);

      if (data.selectedAsset) {
        try {
          await CrmApi.createLead({
            contact_id_write: editingContact.id,
            asset_id: data.selectedAsset.id,
            status: 'new',
          });
        } catch (leadError) {
          console.error('Failed creating lead for updated contact:', leadError);
          toast({
            title: 'לקוח עודכן, שגיאה בליד',
            description: 'הלקוח עודכן בהצלחה אך לא ניתן ליצור ליד עבור הנכס שנבחר.',
            variant: 'destructive',
          });
        }
      }

      toast({
        title: 'לקוח עודכן',
        description: 'פרטי הלקוח עודכנו בהצלחה',
      });

      setEditingContact(null);
      await onRefresh();
      await loadTasks();
    } catch (error: any) {
      toast({
        title: 'שגיאה',
        description: error.message || 'לא ניתן לעדכן את הלקוח',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteContact = async (contact: Contact) => {
    if (!confirm(`האם אתה בטוח שברצונך למחוק את ${contact.name}?`)) {
      return;
    }

    try {
      await CrmApi.deleteContact(contact.id);
      toast({
        title: 'לקוח נמחק',
        description: 'הלקוח נמחק בהצלחה',
      });
      await onRefresh();
      await loadTasks();
    } catch (error) {
      toast({
        title: 'שגיאה',
        description: 'לא ניתן למחוק את הלקוח',
        variant: 'destructive',
      });
    }
  };

  const handleLeadUpdated = async () => {
    await onRefresh();
    await loadTasks();
  };

  const handleDeleteLead = async (leadId: number) => {
    if (!confirm('האם אתה בטוח שברצונך למחוק את הליד?')) {
      return;
    }

    try {
      await CrmApi.deleteLead(leadId);
      toast({
        title: 'ליד נמחק',
        description: 'הליד נמחק בהצלחה',
      });
      await onRefresh();
      await loadTasks();
    } catch (error) {
      toast({
        title: 'שגיאה',
        description: 'לא ניתן למחוק את הליד',
        variant: 'destructive',
      });
    }
  };

  const handleCreateContactTask = async (
    contactId: number,
    data: { title: string; description?: string; due_at?: string; status?: ContactTask['status'] }
  ) => {
    try {
      await CrmApi.createTask({
        title: data.title,
        description: data.description,
        due_at: data.due_at,
        status: data.status,
        contact_id: contactId,
      });
      toast({
        title: 'משימה נוצרה',
        description: 'המשימה החדשה נוספה בהצלחה',
      });
      setIsTaskDialogOpen(false);
      await loadTasks();
    } catch (error) {
      toast({
        title: 'שגיאה',
        description: 'לא ניתן ליצור משימה חדשה',
        variant: 'destructive',
      });
    }
  };

  const handleCompleteTask = async (task: ContactTask) => {
    try {
      await CrmApi.completeTask(task.id);
      toast({
        title: 'משימה הושלמה',
        description: 'המשימה סומנה כהושלמה',
      });
      await loadTasks();
    } catch (error) {
      toast({
        title: 'שגיאה',
        description: 'לא ניתן להשלים את המשימה',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteTask = async (task: ContactTask) => {
    if (!confirm('האם אתה בטוח שברצונך למחוק את המשימה?')) {
      return;
    }

    try {
      await CrmApi.deleteTask(task.id);
      toast({
        title: 'משימה נמחקה',
        description: 'המשימה נמחקה בהצלחה',
      });
      await loadTasks();
    } catch (error) {
      toast({
        title: 'שגיאה',
        description: 'לא ניתן למחוק את המשימה',
        variant: 'destructive',
      });
    }
  };

  if (!contacts.length && !leads.length) {
    return (
      <div className="bg-white rounded-lg border p-8 text-center">
        <div className="flex flex-col gap-4 items-center">
          <div className="text-lg text-muted-foreground">אין נתונים להצגה עדיין</div>
          <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 ms-2 rtl:me-2 rtl:ms-0" />
                הוסף לקוח חדש
              </Button>
            </DialogTrigger>
            <DialogContent className="mx-4 sm:mx-0">
              <DialogHeader>
                <DialogTitle>הוספת לקוח חדש</DialogTitle>
              </DialogHeader>
              <ContactForm onSubmit={handleCreateContact} isLoading={isSubmitting} />
            </DialogContent>
          </Dialog>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between rtl:flex-row-reverse">
        <div className="space-y-1 rtl:text-start">
          <h2 className="text-2xl font-bold">לקוחות ולידים</h2>
          <p className="text-sm text-muted-foreground">
            ניהול לקוחות, מעקב לידים ומשימות במקום אחד
          </p>
        </div>
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 ms-2 rtl:me-2 rtl:ms-0" />
              לקוח חדש
            </Button>
          </DialogTrigger>
          <DialogContent className="mx-4 sm:mx-0">
            <DialogHeader>
              <DialogTitle>הוספת לקוח חדש</DialogTitle>
            </DialogHeader>
            <ContactForm onSubmit={handleCreateContact} isLoading={isSubmitting} />
          </DialogContent>
        </Dialog>
      </div>

      <div className="relative">
        <Search className="absolute end-3 top-1/2 -translate-y-1/2 text-gray-400 h-4 w-4" />
        <Input
          placeholder="חיפוש לפי לקוח, תגית או נכס..."
          value={searchQuery}
          onChange={(event) => setSearchQuery(event.target.value)}
          className="pe-10"
        />
      </div>

      <div className="bg-white rounded-lg border overflow-x-auto">
        <div className="min-w-full">
          <Table className="table-auto min-w-[1024px]">
            <TableHeader>
              <TableRow>
                <TableHead className="w-10"></TableHead>
                <TableHead className="min-w-[180px] rtl:text-start">לקוח</TableHead>
                <TableHead className="min-w-[200px] rtl:text-start">נכסים ותחומי עניין</TableHead>
                <TableHead className="min-w-[140px] rtl:text-start">סטטוס לידים</TableHead>
                <TableHead className="min-w-[140px] rtl:text-start">משימות</TableHead>
                <TableHead className="min-w-[140px] rtl:text-start">פעילות אחרונה</TableHead>
                <TableHead className="min-w-[140px] rtl:text-start">פעולות</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredRows.map(({ contact, leads: contactLeads }) => {
                const contactTasks = tasksByContact.get(contact.id) || [];
                const pendingTasks = contactTasks.filter((task) => task.status !== 'completed');
                const completedTasks = contactTasks.filter((task) => task.status === 'completed');
                const uniqueAssets = Array.from(
                  new Set(contactLeads.map((lead) => lead.asset_address))
                );
                const activeStatuses = Array.from(
                  new Set(contactLeads.map((lead) => lead.status))
                );
                const isExpanded = expandedRows.has(contact.id);

                return (
                  <React.Fragment key={contact.id}>
                    <TableRow>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => toggleRowExpansion(contact.id)}
                          className="h-8 w-8 p-0"
                          aria-label={isExpanded ? 'סגירת פרטי לקוח' : 'פתיחת פרטי לקוח'}
                        >
                          {isExpanded ? (
                            <ChevronDown className="h-3 w-3" />
                          ) : (
                            <ChevronRight className="h-3 w-3 rtl:rotate-180" />
                          )}
                        </Button>
                      </TableCell>
                      <TableCell>
                        <div className="rtl:text-start">
                          <div className="font-medium">{contact.name}</div>
                          <div className="text-xs text-muted-foreground space-y-0.5">
                            {contact.email && <div>{contact.email}</div>}
                            {contact.phone && <div>{contact.phone}</div>}
                          </div>
                          {contact.tags.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {contact.tags.map((tag) => (
                                <Badge key={tag} variant="secondary" className="text-xs">
                                  {tag}
                                </Badge>
                              ))}
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        {uniqueAssets.length === 0 ? (
                          <span className="text-sm text-muted-foreground rtl:text-start">אין לידים משויכים</span>
                        ) : (
                          <div className="space-y-1 rtl:text-start">
                            {uniqueAssets.slice(0, 2).map((asset) => (
                              <div key={asset} className="text-sm">{asset}</div>
                            ))}
                            {uniqueAssets.length > 2 && (
                              <div className="text-xs text-muted-foreground">ועוד {uniqueAssets.length - 2} נכסים...</div>
                            )}
                          </div>
                        )}
                      </TableCell>
                      <TableCell>
                        {contactLeads.length === 0 ? (
                          <span className="text-sm text-muted-foreground rtl:text-start">אין לידים</span>
                        ) : (
                          <div className="flex flex-wrap gap-1 rtl:flex-row-reverse">
                            {activeStatuses.map((status) => (
                              <LeadStatusBadge key={status} status={status} />
                            ))}
                          </div>
                        )}
                      </TableCell>
                      <TableCell>
                        {isTasksLoading ? (
                          <div className="flex items-center gap-2 text-sm text-muted-foreground rtl:flex-row-reverse">
                            <ButtonLoader size="sm" />
                            טוען משימות...
                          </div>
                        ) : (
                          <div className="flex flex-col rtl:text-start text-sm">
                            <span>{pendingTasks.length} פתוחות</span>
                            <span className="text-muted-foreground">{completedTasks.length} הושלמו</span>
                          </div>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="text-sm rtl:text-start">
                          {formatDate(getLastActivity({ contact, leads: contactLeads }))}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2 rtl:flex-row-reverse">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setEditingContact(contact);
                              setIsCreateDialogOpen(false);
                            }}
                          >
                            <Edit className="h-3 w-3 ms-1 rtl:me-1 rtl:ms-0" /> ערוך
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setActiveTaskContact(contact.id);
                              setIsTaskDialogOpen(true);
                            }}
                          >
                            <Plus className="h-3 w-3 ms-1 rtl:me-1 rtl:ms-0" /> משימה
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDeleteContact(contact)}
                          >
                            <Trash2 className="h-3 w-3 ms-1 rtl:me-1 rtl:ms-0" /> מחק
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>

                    {isExpanded && (
                      <TableRow>
                        <TableCell colSpan={7} className="bg-gray-50">
                          <div className="p-4 space-y-6 rtl:text-start">
                            <section className="space-y-2">
                              <h3 className="font-semibold text-base">פרטי לקוח</h3>
                              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                                <div>
                                  <span className="text-muted-foreground">שם:</span> {contact.name}
                                </div>
                                {contact.email && (
                                  <div>
                                    <span className="text-muted-foreground">אימייל:</span> {contact.email}
                                  </div>
                                )}
                                {contact.phone && (
                                  <div>
                                    <span className="text-muted-foreground">טלפון:</span> {contact.phone}
                                  </div>
                                )}
                                {contact.equity && (
                                  <div>
                                    <span className="text-muted-foreground">הון עצמי:</span> {formatCurrency(contact.equity)}
                                  </div>
                                )}
                                {contact.city && (
                                  <div>
                                    <span className="text-muted-foreground">עיר מועדפת:</span> {contact.city}
                                  </div>
                                )}
                                {contact.asset_type && (
                                  <div>
                                    <span className="text-muted-foreground">סוג נכס:</span> {contact.asset_type}
                                  </div>
                                )}
                                {contact.notes && (
                                  <div className="sm:col-span-2">
                                    <span className="text-muted-foreground">הערות:</span>
                                    <p className="mt-1 whitespace-pre-wrap">{contact.notes}</p>
                                  </div>
                                )}
                              </div>
                            </section>

                            <section className="space-y-3">
                              <div className="flex items-center justify-between">
                                <h3 className="font-semibold text-base">לידים משויכים</h3>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => window.open('/assets', '_blank')}
                                >
                                  <Plus className="h-3 w-3 ms-1 rtl:me-1 rtl:ms-0" /> צור ליד חדש
                                </Button>
                              </div>

                              {contactLeads.length === 0 ? (
                                <div className="text-sm text-muted-foreground">לא קיימים לידים עבור לקוח זה</div>
                              ) : (
                                <div className="space-y-3">
                                  {contactLeads.map((lead) => (
                                    <div key={lead.id} className="bg-white border rounded-md p-4">
                                      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between rtl:flex-row-reverse">
                                        <div className="flex-1 space-y-1 rtl:text-start">
                                          <div className="font-medium flex items-center gap-2 rtl:flex-row-reverse">
                                            <span>{lead.asset_address}</span>
                                            <Button
                                              variant="link"
                                              size="sm"
                                              className="p-0 h-auto"
                                              onClick={() => window.open(`/assets/${lead.asset_id_read}`, '_blank')}
                                            >
                                              <ExternalLink className="h-3 w-3 ms-1 rtl:me-1 rtl:ms-0" /> צפה בנכס
                                            </Button>
                                          </div>
                                          <div className="text-xs text-muted-foreground flex flex-wrap gap-3 rtl:flex-row-reverse">
                                            {lead.asset_price && <span>מחיר: {formatCurrency(lead.asset_price)}</span>}
                                            {lead.asset_rooms && <span>חדרים: {lead.asset_rooms}</span>}
                                            {lead.asset_area && <span>שטח: {lead.asset_area} מ״ר</span>}
                                          </div>
                                        </div>
                                        <div className="flex items-center gap-2 rtl:flex-row-reverse">
                                          <LeadStatusBadge status={lead.status} />
                                          <LeadRowActions
                                            lead={lead}
                                            onUpdate={handleLeadUpdated}
                                            onDelete={handleDeleteLead}
                                          />
                                        </div>
                                      </div>

                                      <div className="mt-3">
                                        <LeadTaskSummary lead={lead} compact={false} />
                                      </div>

                                      {lead.notes.length > 0 && (
                                        <div className="mt-3 space-y-2">
                                          <h4 className="text-sm font-medium">הערות</h4>
                                          {lead.notes.map((note, index) => (
                                            <div key={index} className="bg-gray-50 rounded p-2 text-sm">
                                              <div className="text-xs text-muted-foreground mb-1">{formatDate(note.ts)}</div>
                                              <div>{note.text}</div>
                                            </div>
                                          ))}
                                        </div>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              )}
                            </section>

                            <section className="space-y-3">
                              <div className="flex items-center justify-between">
                                <h3 className="font-semibold text-base">משימות לקוח</h3>
                                <Button
                                  size="sm"
                                  onClick={() => {
                                    setActiveTaskContact(contact.id);
                                    setIsTaskDialogOpen(true);
                                  }}
                                >
                                  <Plus className="h-3 w-3 ms-1 rtl:me-1 rtl:ms-0" /> משימה חדשה
                                </Button>
                              </div>

                              {contactTasks.length === 0 ? (
                                <div className="text-sm text-muted-foreground">לא קיימות משימות עבור לקוח זה</div>
                              ) : (
                                <div className="space-y-2">
                                  {contactTasks.map((task) => (
                                    <div key={task.id} className="bg-white border rounded-md p-3">
                                      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between rtl:flex-row-reverse">
                                        <div className="rtl:text-start">
                                          <div className="font-medium text-sm">{task.title}</div>
                                          {task.description && (
                                            <div className="text-xs text-muted-foreground mt-1">{task.description}</div>
                                          )}
                                          <div className="text-xs text-muted-foreground mt-1 space-x-2 space-x-reverse">
                                            <span>סטטוס: {taskStatusLabel(task.status)}</span>
                                            {task.due_at && <span>יעד: {formatDate(task.due_at)}</span>}
                                          </div>
                                        </div>
                                        <div className="flex items-center gap-2 rtl:flex-row-reverse">
                                          {task.status !== 'completed' && (
                                            <Button
                                              size="sm"
                                              variant="outline"
                                              onClick={() => handleCompleteTask(task)}
                                            >
                                              <CheckSquare className="h-3 w-3 ms-1 rtl:me-1 rtl:ms-0" /> סמן הושלם
                                            </Button>
                                          )}
                                          <Button
                                            size="sm"
                                            variant="outline"
                                            onClick={() => handleDeleteTask(task)}
                                          >
                                            <Trash2 className="h-3 w-3 ms-1 rtl:me-1 rtl:ms-0" /> מחק
                                          </Button>
                                        </div>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </section>
                          </div>
                        </TableCell>
                      </TableRow>
                    )}
                  </React.Fragment>
                );
              })}
            </TableBody>
          </Table>
        </div>
      </div>

      <Dialog open={!!editingContact} onOpenChange={(open) => !open && setEditingContact(null)}>
        <DialogContent className="mx-4 sm:mx-0">
          <DialogHeader>
            <DialogTitle>עריכת לקוח</DialogTitle>
          </DialogHeader>
          {editingContact ? (
            <ContactForm
              initialData={editingContact}
              onSubmit={handleUpdateContact}
              onCancel={() => setEditingContact(null)}
              isLoading={isSubmitting}
            />
          ) : (
            <PageLoader message="טוען טופס..." showLogo={false} />
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={isTaskDialogOpen} onOpenChange={(open) => setIsTaskDialogOpen(open)}>
        <DialogContent className="mx-4 sm:mx-0">
          <DialogHeader>
            <DialogTitle>משימה חדשה ללקוח</DialogTitle>
          </DialogHeader>
          {activeTaskContact ? (
            <TaskForm
              onSubmit={async (data) => {
                await handleCreateContactTask(activeTaskContact, data);
              }}
              onCancel={() => setIsTaskDialogOpen(false)}
            />
          ) : (
            <PageLoader message="טוען..." showLogo={false} />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function getLastActivity(row: CombinedRow): Date {
  if (row.leads.length === 0) {
    return new Date(row.contact.updated_at || row.contact.created_at);
  }

  const maxLeadDate = row.leads.reduce((latest, lead) => {
    const leadDate = new Date(lead.last_activity_at || lead.created_at);
    return leadDate > latest ? leadDate : latest;
  }, new Date(row.contact.updated_at || row.contact.created_at));

  return maxLeadDate;
}

function formatDate(value: string | Date): string {
  const date = typeof value === 'string' ? new Date(value) : value;
  if (Number.isNaN(date.getTime())) {
    return '-';
  }
  return date.toLocaleDateString('he-IL');
}

function formatCurrency(value?: number | string | null): string {
  if (value === null || value === undefined || value === '') {
    return '-';
  }

  const numeric = typeof value === 'string' ? Number(value) : value;
  if (!numeric || Number.isNaN(numeric)) {
    return '-';
  }

  return new Intl.NumberFormat('he-IL', {
    style: 'currency',
    currency: 'ILS',
    maximumFractionDigits: 0,
  }).format(numeric);
}

function taskStatusLabel(status: ContactTask['status']): string {
  switch (status) {
    case 'completed':
      return 'הושלם';
    case 'cancelled':
      return 'בוטל';
    default:
      return 'בתהליך';
  }
}
