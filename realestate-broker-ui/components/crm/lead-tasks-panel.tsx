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
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu';
import { 
  CheckSquare, 
  Plus, 
  MoreHorizontal, 
  Clock, 
  CheckCircle, 
  XCircle,
  Calendar,
  User,
  X
} from 'lucide-react';
import { Lead, ContactTask, TaskStatus, CrmApi, CreateTaskData, UpdateTaskData } from '@/lib/api/crm';
import { useToast } from '@/hooks/use-toast';
import { TaskForm } from './task-form';
import { PageLoader } from '@/components/ui/page-loader';
import { clearTaskCache } from './lead-task-summary';

interface LeadTasksPanelProps {
  lead: Lead;
  onClose?: () => void;
}

const statusOptions: { value: TaskStatus; label: string; color: string }[] = [
  { value: 'pending', label: 'ממתין', color: 'bg-yellow-100 text-yellow-800' },
  { value: 'completed', label: 'הושלם', color: 'bg-green-100 text-green-800' },
  { value: 'cancelled', label: 'בוטל', color: 'bg-red-100 text-red-800' },
];

export function LeadTasksPanel({ lead, onClose }: LeadTasksPanelProps) {
  const [tasks, setTasks] = useState<ContactTask[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState<ContactTask | null>(null);
  const { toast } = useToast();

  const loadTasks = useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await CrmApi.getLeadTasks(lead.id);
      setTasks(data);
    } catch (error) {
      toast({
        title: 'שגיאה',
        description: 'לא ניתן לטעון את רשימת המשימות',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  }, [lead.id, toast]);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  const handleCreateTask = async (data: CreateTaskData | UpdateTaskData) => {
    try {
      // Ensure we have the required fields for task creation
      const createData: CreateTaskData = {
        title: data.title || '',
        description: data.description,
        due_at: data.due_at,
        contact_id: lead.contact_id,
        lead_id_write: lead.id,
        status: data.status || 'pending',
      };
      
      await CrmApi.createTask(createData);
      await loadTasks();
      clearTaskCache(lead.id); // Clear cache to update summary
      setIsCreateModalOpen(false);
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
      clearTaskCache(lead.id); // Clear cache to update summary
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
      clearTaskCache(lead.id); // Clear cache to update summary
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
    setIsEditModalOpen(true);
  };

  const handleUpdateTask = async (data: CreateTaskData | UpdateTaskData) => {
    if (!selectedTask) return;

    try {
      await CrmApi.updateTask(selectedTask.id, data);
      await loadTasks();
      clearTaskCache(lead.id); // Clear cache to update summary
      setIsEditModalOpen(false);
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

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'ללא תאריך';
    return new Date(dateString).toLocaleDateString('he-IL');
  };

  const getStatusInfo = (status: TaskStatus) => {
    return statusOptions.find(option => option.value === status) || statusOptions[0];
  };

  const getStatusCounts = () => {
    const counts = {
      pending: 0,
      completed: 0,
      cancelled: 0,
    };

    tasks.forEach(task => {
      counts[task.status]++;
    });

    return counts;
  };

  const statusCounts = getStatusCounts();

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckSquare className="h-5 w-5" />
            משימות לליד
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
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="min-w-0 flex-1">
            <CardTitle className="flex items-center gap-2 text-base sm:text-lg">
              <CheckSquare className="h-4 w-4 sm:h-5 sm:w-5" />
              משימות לליד
            </CardTitle>
            <CardDescription className="text-sm break-words">
              משימות עבור {lead.contact.name} - {lead.asset_address}
            </CardDescription>
          </div>
          <div className="flex gap-2 w-full sm:w-auto">
            <Dialog open={isCreateModalOpen} onOpenChange={setIsCreateModalOpen}>
              <DialogTrigger asChild>
                <Button size="sm" className="flex-1 sm:flex-none">
                  <Plus className="h-4 w-4 mr-2" />
                  <span className="hidden sm:inline">משימה חדשה</span>
                  <span className="sm:hidden">חדשה</span>
                </Button>
              </DialogTrigger>
              <DialogContent className="mx-4 sm:mx-0">
                <DialogHeader>
                  <DialogTitle>יצירת משימה חדשה</DialogTitle>
                </DialogHeader>
                <TaskForm
                  onSubmit={handleCreateTask}
                  onCancel={() => setIsCreateModalOpen(false)}
                  isLoading={false}
                />
              </DialogContent>
            </Dialog>
            {onClose && (
              <Button size="sm" variant="outline" onClick={onClose} className="h-9 w-9 p-0 sm:h-9 sm:w-auto sm:px-3">
                <X className="h-4 w-4" />
                <span className="hidden sm:inline mr-2">סגור</span>
              </Button>
            )}
          </div>
        </div>

        {/* Status Summary */}
        <div className="flex gap-2 flex-wrap">
          {statusOptions.map(({ value, label, color }) => (
            <Badge key={value} className={`${color} text-xs`}>
              {label}: {statusCounts[value]}
            </Badge>
          ))}
        </div>
      </CardHeader>

      <CardContent>
        {tasks.length === 0 ? (
          <div className="text-center py-6 sm:py-8 text-muted-foreground">
            <CheckSquare className="h-10 w-10 sm:h-12 sm:w-12 mx-auto mb-4 opacity-50" />
            <p className="text-sm sm:text-base">אין משימות עבור ליד זה</p>
            <p className="text-xs sm:text-sm">צור משימה חדשה כדי להתחיל</p>
          </div>
        ) : (
          <div className="border rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-right min-w-[150px]">כותרת</TableHead>
                    <TableHead className="text-right min-w-[120px] hidden sm:table-cell">תיאור</TableHead>
                    <TableHead className="text-right min-w-[100px] hidden md:table-cell">תאריך יעד</TableHead>
                    <TableHead className="text-right min-w-[100px] hidden sm:table-cell">סטטוס</TableHead>
                    <TableHead className="text-right min-w-[100px] hidden lg:table-cell">נוצר</TableHead>
                    <TableHead className="text-right min-w-[80px]">פעולות</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {tasks.map((task) => {
                    const statusInfo = getStatusInfo(task.status);
                    return (
                      <TableRow key={task.id}>
                        <TableCell className="text-right">
                          <div className="font-medium text-sm sm:text-base">{task.title}</div>
                          <div className="text-xs text-muted-foreground sm:hidden">
                            <Badge className={`${statusInfo.color} text-xs`}>
                              {statusInfo.label}
                            </Badge>
                          </div>
                        </TableCell>
                        <TableCell className="text-right hidden sm:table-cell">
                          <div className="text-xs sm:text-sm text-muted-foreground max-w-xs truncate">
                            {task.description || 'ללא תיאור'}
                          </div>
                        </TableCell>
                        <TableCell className="text-right hidden md:table-cell">
                          <div className="flex items-center gap-1 text-xs sm:text-sm">
                            <Calendar className="h-3 w-3 sm:h-4 sm:w-4" />
                            {formatDate(task.due_at)}
                          </div>
                        </TableCell>
                        <TableCell className="text-right hidden sm:table-cell">
                          <Badge className={`${statusInfo.color} text-xs`}>
                            {statusInfo.label}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right hidden lg:table-cell">
                          <div className="text-xs sm:text-sm text-muted-foreground">
                            {formatDate(task.created_at)}
                          </div>
                        </TableCell>
                        <TableCell className="text-right">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                                <MoreHorizontal className="h-3 w-3 sm:h-4 sm:w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="w-48">
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
      </CardContent>

      {/* Edit Task Modal */}
      <Dialog open={isEditModalOpen} onOpenChange={setIsEditModalOpen}>
        <DialogContent className="mx-4 sm:mx-0">
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
                setIsEditModalOpen(false);
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
