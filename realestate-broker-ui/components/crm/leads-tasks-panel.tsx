'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/Badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu';
import { 
  Users, 
  Plus, 
  ExternalLink, 
  MessageSquare,
  CheckSquare,
  MoreHorizontal,
  Clock,
  CheckCircle,
  XCircle,
  Calendar,
  User
} from 'lucide-react';
import { Lead, ContactTask, TaskStatus, CrmApi, CreateTaskData, UpdateTaskData } from '@/lib/api/crm';
import { LeadStatusBadge } from './lead-status-badge';
import { LeadRowActions } from './lead-row-actions';
import { AssignContactModal } from './assign-contact-modal';
import { TaskForm } from './task-form';
import { useToast } from '@/hooks/use-toast';
import { PageLoader } from '@/components/ui/page-loader';

interface LeadsTasksPanelProps {
  assetId: number;
  assetAddress?: string;
}

const statusOptions: { value: TaskStatus; label: string; color: string }[] = [
  { value: 'pending', label: 'ממתין', color: 'bg-yellow-100 text-yellow-800' },
  { value: 'completed', label: 'הושלם', color: 'bg-green-100 text-green-800' },
  { value: 'cancelled', label: 'בוטל', color: 'bg-red-100 text-red-800' },
];

export function LeadsTasksPanel({ assetId, assetAddress }: LeadsTasksPanelProps) {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [allTasks, setAllTasks] = useState<ContactTask[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [isCreateTaskModalOpen, setIsCreateTaskModalOpen] = useState(false);
  const [isEditTaskModalOpen, setIsEditTaskModalOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState<ContactTask | null>(null);
  const [selectedLeadForTask, setSelectedLeadForTask] = useState<Lead | null>(null);
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

  const loadTasks = useCallback(async () => {
    try {
      const tasks = await CrmApi.getTasks({ lead: undefined }); // Get all tasks for this user
      // Filter tasks that belong to leads for this asset
      const assetLeadIds = leads.map(lead => lead.id);
      const relevantTasks = tasks.filter(task => 
        task.lead_id && assetLeadIds.includes(task.lead_id)
      );
      setAllTasks(relevantTasks);
    } catch (error) {
      toast({
        title: 'שגיאה',
        description: 'לא ניתן לטעון את רשימת המשימות',
        variant: 'destructive',
      });
    }
  }, [leads, toast]);

  useEffect(() => {
    loadLeads();
  }, [loadLeads]);

  useEffect(() => {
    if (leads.length > 0) {
      loadTasks();
    }
  }, [leads, loadTasks]);

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

  const handleCreateTask = async (data: CreateTaskData | UpdateTaskData) => {
    try {
      // Type guard to ensure we have CreateTaskData
      if ('contact_id' in data) {
        await CrmApi.createTask(data);
      } else {
        throw new Error('Invalid data for task creation');
      }
      await loadTasks();
      setIsCreateTaskModalOpen(false);
      setSelectedLeadForTask(null);
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

  const handleCompleteTask = async (task: ContactTask) => {
    try {
      await CrmApi.completeTask(task.id);
      await loadTasks();
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

  const handleDeleteTask = async (task: ContactTask) => {
    if (!confirm(`האם אתה בטוח שברצונך למחוק את המשימה "${task.title}"?`)) {
      return;
    }

    try {
      await CrmApi.deleteTask(task.id);
      await loadTasks();
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

  const handleEditTask = (task: ContactTask) => {
    setSelectedTask(task);
    setIsEditTaskModalOpen(true);
  };

  const handleUpdateTask = async (data: CreateTaskData | UpdateTaskData) => {
    if (!selectedTask) return;

    try {
      await CrmApi.updateTask(selectedTask.id, data);
      await loadTasks();
      setIsEditTaskModalOpen(false);
      setSelectedTask(null);
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

  const getTaskStatusCounts = () => {
    const counts = {
      pending: 0,
      completed: 0,
      cancelled: 0,
    };

    allTasks.forEach(task => {
      counts[task.status]++;
    });

    return counts;
  };

  const statusCounts = getStatusCounts();
  const taskStatusCounts = getTaskStatusCounts();

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            לידים ומשימות
          </CardTitle>
        </CardHeader>
        <CardContent>
          <PageLoader />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between rtl:flex-row-reverse">
          <div className="rtl:text-right">
            <CardTitle className="flex items-center gap-2 rtl:flex-row-reverse">
              <Users className="h-5 w-5" />
              לידים ומשימות
            </CardTitle>
            <CardDescription>
              ניהול לידים ומשימות עבור נכס זה
            </CardDescription>
          </div>
          <div className="flex gap-2">
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
            <Dialog open={isCreateTaskModalOpen} onOpenChange={setIsCreateTaskModalOpen}>
              <DialogTrigger asChild>
                <Button size="sm" variant="outline">
                  <CheckSquare className="h-4 w-4 ml-2 rtl:mr-2 rtl:ml-0" />
                  משימה חדשה
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>יצירת משימה חדשה</DialogTitle>
                </DialogHeader>
                <TaskForm
                  onSubmit={handleCreateTask}
                  onCancel={() => {
                    setIsCreateTaskModalOpen(false);
                    setSelectedLeadForTask(null);
                  }}
                  isLoading={false}
                />
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <Tabs defaultValue="leads" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="leads" className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              לידים ({leads.length})
            </TabsTrigger>
            <TabsTrigger value="tasks" className="flex items-center gap-2">
              <CheckSquare className="h-4 w-4" />
              משימות ({allTasks.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="leads" className="space-y-4">
            {leads.length === 0 ? (
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
                              onShowTasks={() => {}} // No-op since this panel already shows tasks
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>
            )}
          </TabsContent>

          <TabsContent value="tasks" className="space-y-4">
            {allTasks.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <CheckSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>אין משימות עבור לידים אלו</p>
                <p className="text-sm">צור משימה חדשה כדי להתחיל</p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Task Status Summary */}
                <div className="flex gap-2 flex-wrap">
                  {statusOptions.map(({ value, label, color }) => (
                    <Badge key={value} className={color}>
                      {label}: {taskStatusCounts[value]}
                    </Badge>
                  ))}
                </div>

                {/* Tasks Table */}
                <div className="border rounded-lg">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="text-right">כותרת</TableHead>
                        <TableHead className="text-right">לקוח</TableHead>
                        <TableHead className="text-right">תאריך יעד</TableHead>
                        <TableHead className="text-right">סטטוס</TableHead>
                        <TableHead className="text-right">נוצר</TableHead>
                        <TableHead className="text-right">פעולות</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {allTasks.map((task) => {
                        const statusInfo = statusOptions.find(opt => opt.value === task.status) || statusOptions[0];
                        return (
                          <TableRow key={task.id}>
                            <TableCell className="text-right">
                              <div className="font-medium">{task.title}</div>
                              {task.description && (
                                <div className="text-sm text-muted-foreground max-w-xs truncate">
                                  {task.description}
                                </div>
                              )}
                            </TableCell>
                            <TableCell className="text-right">
                              <div className="flex items-center gap-1 text-sm">
                                <User className="h-4 w-4" />
                                {task.contact.name}
                              </div>
                            </TableCell>
                            <TableCell className="text-right">
                              <div className="flex items-center gap-1 text-sm">
                                <Calendar className="h-4 w-4" />
                                {task.due_at ? formatDate(task.due_at) : 'ללא תאריך'}
                              </div>
                            </TableCell>
                            <TableCell className="text-right">
                              <Badge className={statusInfo.color}>
                                {statusInfo.label}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-right">
                              <div className="text-sm text-muted-foreground">
                                {formatDate(task.created_at)}
                              </div>
                            </TableCell>
                            <TableCell className="text-right">
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <Button variant="ghost" size="sm">
                                    <MoreHorizontal className="h-4 w-4" />
                                  </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                  {task.status === 'pending' && (
                                    <DropdownMenuItem onClick={() => handleCompleteTask(task)}>
                                      <CheckCircle className="h-4 w-4 mr-2" />
                                      סמן כהושלם
                                    </DropdownMenuItem>
                                  )}
                                  <DropdownMenuItem onClick={() => handleEditTask(task)}>
                                    <Clock className="h-4 w-4 mr-2" />
                                    ערוך
                                  </DropdownMenuItem>
                                  <DropdownMenuItem 
                                    onClick={() => handleDeleteTask(task)}
                                    className="text-red-600"
                                  >
                                    <XCircle className="h-4 w-4 mr-2" />
                                    מחק
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </div>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>

      {/* Edit Task Modal */}
      <Dialog open={isEditTaskModalOpen} onOpenChange={setIsEditTaskModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>עריכת משימה</DialogTitle>
          </DialogHeader>
          {selectedTask && (
            <TaskForm
              initialData={{
                title: selectedTask.title,
                description: selectedTask.description,
                due_at: selectedTask.due_at || undefined,
                status: selectedTask.status,
              }}
              onSubmit={handleUpdateTask}
              onCancel={() => {
                setIsEditTaskModalOpen(false);
                setSelectedTask(null);
              }}
              isLoading={false}
            />
          )}
        </DialogContent>
      </Dialog>
    </Card>
  );
}
