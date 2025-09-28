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
import { Search, ExternalLink, Plus, ChevronDown, ChevronRight, CheckSquare, Edit, Trash2 } from 'lucide-react';
import { Lead, CrmApi, ContactTask, CreateTaskData, UpdateTaskData } from '@/lib/api/crm';
import { LeadStatusBadge } from '@/components/crm/lead-status-badge';
import { LeadRowActions } from '@/components/crm/lead-row-actions';
import { LeadTasksPanel } from '@/components/crm/lead-tasks-panel';
import { LeadTaskSummary } from '@/components/crm/lead-task-summary';
import { TaskForm } from '@/components/crm/task-form';
import { useToast } from '@/hooks/use-toast';
import DashboardLayout from '@/components/layout/dashboard-layout';
import { PageLoader } from '@/components/ui/page-loader';
import { Skeleton } from '@/components/ui/skeleton';
import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from '@/components/ui/breadcrumb';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import Link from 'next/link';

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLeadForTasks, setSelectedLeadForTasks] = useState<Lead | null>(null);
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
  const [leadTasks, setLeadTasks] = useState<Map<number, ContactTask[]>>(new Map());
  const [isCreateTaskModalOpen, setIsCreateTaskModalOpen] = useState<number | null>(null);
  const [editingTask, setEditingTask] = useState<ContactTask | null>(null);
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

  const toggleRowExpansion = (leadId: number) => {
    setExpandedRows(prev => {
      const newSet = new Set(prev);
      if (newSet.has(leadId)) {
        newSet.delete(leadId);
      } else {
        newSet.add(leadId);
        // Load tasks when expanding
        loadTasksForLead(leadId);
      }
      return newSet;
    });
  };

  const loadTasksForLead = async (leadId: number) => {
    try {
      const tasks = await CrmApi.getLeadTasks(leadId);
      setLeadTasks(prev => new Map(prev.set(leadId, tasks)));
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
        contact_id: leads.find(l => l.id === leadId)?.contact_id || 0,
        lead_id_write: leadId,
        status: data.status || 'pending',
      };
      
      await CrmApi.createTask(createData);
      await loadTasksForLead(leadId);
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
                <TableHead className="w-8"></TableHead>
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
                <>
                  <TableRow key={lead.id}>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleRowExpansion(lead.id)}
                        className="h-6 w-6 p-0"
                      >
                        {expandedRows.has(lead.id) ? (
                          <ChevronDown className="h-3 w-3" />
                        ) : (
                          <ChevronRight className="h-3 w-3" />
                        )}
                      </Button>
                    </TableCell>
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
                    <div className="flex items-center gap-1">
                      {leadTasks.get(lead.id) ? (
                        <>
                          {leadTasks.get(lead.id)!.filter(t => t.status === 'pending').length > 0 && (
                            <Badge variant="secondary" className="text-xs">
                              {leadTasks.get(lead.id)!.filter(t => t.status === 'pending').length} ממתינות
                            </Badge>
                          )}
                          {leadTasks.get(lead.id)!.filter(t => t.status === 'completed').length > 0 && (
                            <Badge variant="outline" className="text-xs">
                              {leadTasks.get(lead.id)!.filter(t => t.status === 'completed').length} הושלמו
                            </Badge>
                          )}
                          {leadTasks.get(lead.id)!.length === 0 && (
                            <span className="text-xs text-muted-foreground">אין משימות</span>
                          )}
                        </>
                      ) : (
                        <span className="text-xs text-muted-foreground">טוען...</span>
                      )}
                    </div>
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
                
                {/* Expanded Row Content */}
                {expandedRows.has(lead.id) && (
                  <TableRow>
                    <TableCell colSpan={7} className="bg-gray-50 p-4">
                      <div className="space-y-4">
                        {/* Notes Section */}
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
                        
                        {/* Contact Details */}
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
                        
                        {/* Asset Details */}
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
                              <span className="text-muted-foreground">שטח:</span> {lead.asset_area ? `${lead.asset_area} מ״ר` : '-'}
                            </div>
                          </div>
                        </div>
                        
                        {/* Task Management */}
                        <div>
                          <div className="flex items-center justify-between mb-3">
                            <h4 className="font-medium">ניהול משימות</h4>
                            <Dialog open={isCreateTaskModalOpen === lead.id} onOpenChange={(open) => setIsCreateTaskModalOpen(open ? lead.id : null)}>
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
                            
                            {/* Edit Task Dialog */}
                            <Dialog open={!!editingTask} onOpenChange={(open) => !open && setEditingTask(null)}>
                              <DialogContent className="mx-4 sm:mx-0">
                                <DialogHeader>
                                  <DialogTitle>עריכת משימה</DialogTitle>
                                </DialogHeader>
                                <TaskForm
                                  initialData={editingTask ? {
                                    title: editingTask.title,
                                    description: editingTask.description,
                                    due_at: editingTask.due_at || undefined,
                                    status: editingTask.status
                                  } : undefined}
                                  onSubmit={(data) => editingTask && handleEditTask(lead.id, data)}
                                  onCancel={() => setEditingTask(null)}
                                />
                              </DialogContent>
                            </Dialog>
                          </div>
                          
                          {/* Tasks List */}
                          <div className="space-y-2">
                            {leadTasks.get(lead.id)?.length === 0 ? (
                              <div className="text-sm text-muted-foreground text-center py-4">
                                אין משימות עדיין
                              </div>
                            ) : (
                              leadTasks.get(lead.id)?.map((task) => (
                                <div key={task.id} className="flex items-center justify-between p-3 bg-white rounded border">
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
                                      variant={task.status === 'completed' ? 'default' : task.status === 'pending' ? 'secondary' : 'destructive'}
                                      className="text-xs"
                                    >
                                      {task.status === 'completed' ? 'הושלם' : task.status === 'pending' ? 'ממתין' : 'בוטל'}
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
              </>
              ))}
            </TableBody>
          </Table>
        </div>
      )}


      </div>
    </DashboardLayout>
  );
}
