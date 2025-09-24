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
      // Type guard to ensure we have CreateTaskData
      if ('contact_id' in data) {
        await CrmApi.createTask({
          ...data,
          contact_id: lead.contact_id,
          lead_id: lead.id,
        });
      } else {
        throw new Error('Invalid data for task creation');
      }
      await loadTasks();
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
    setIsEditModalOpen(true);
  };

  const handleUpdateTask = async (data: CreateTaskData | UpdateTaskData) => {
    if (!selectedTask) return;

    try {
      await CrmApi.updateTask(selectedTask.id, data);
      await loadTasks();
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
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <CheckSquare className="h-5 w-5" />
              משימות לליד
            </CardTitle>
            <CardDescription>
              משימות עבור {lead.contact.name} - {lead.asset_address}
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Dialog open={isCreateModalOpen} onOpenChange={setIsCreateModalOpen}>
              <DialogTrigger asChild>
                <Button size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  משימה חדשה
                </Button>
              </DialogTrigger>
              <DialogContent>
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
              <Button size="sm" variant="outline" onClick={onClose}>
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>

        {/* Status Summary */}
        <div className="flex gap-2 flex-wrap">
          {statusOptions.map(({ value, label, color }) => (
            <Badge key={value} className={color}>
              {label}: {statusCounts[value]}
            </Badge>
          ))}
        </div>
      </CardHeader>

      <CardContent>
        {tasks.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <CheckSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>אין משימות עבור ליד זה</p>
            <p className="text-sm">צור משימה חדשה כדי להתחיל</p>
          </div>
        ) : (
          <div className="border rounded-lg">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-right">כותרת</TableHead>
                  <TableHead className="text-right">תיאור</TableHead>
                  <TableHead className="text-right">תאריך יעד</TableHead>
                  <TableHead className="text-right">סטטוס</TableHead>
                  <TableHead className="text-right">נוצר</TableHead>
                  <TableHead className="text-right">פעולות</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {tasks.map((task) => {
                  const statusInfo = getStatusInfo(task.status);
                  return (
                    <TableRow key={task.id}>
                      <TableCell className="text-right">
                        <div className="font-medium">{task.title}</div>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="text-sm text-muted-foreground max-w-xs truncate">
                          {task.description || 'ללא תיאור'}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center gap-1 text-sm">
                          <Calendar className="h-4 w-4" />
                          {formatDate(task.due_at)}
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
        )}
      </CardContent>

      {/* Edit Task Modal */}
      <Dialog open={isEditModalOpen} onOpenChange={setIsEditModalOpen}>
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
