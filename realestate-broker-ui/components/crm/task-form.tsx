'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { CalendarIcon } from 'lucide-react';
import { CreateTaskData, UpdateTaskData, TaskStatus } from '@/lib/api/crm';

interface TaskFormProps {
  initialData?: Partial<CreateTaskData>;
  onSubmit: (data: CreateTaskData | UpdateTaskData) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

const statusOptions: { value: TaskStatus; label: string }[] = [
  { value: 'pending', label: 'ממתין' },
  { value: 'completed', label: 'הושלם' },
  { value: 'cancelled', label: 'בוטל' },
];

export function TaskForm({ 
  initialData = {}, 
  onSubmit, 
  onCancel, 
  isLoading = false 
}: TaskFormProps) {
  const [formData, setFormData] = useState({
    title: initialData.title || '',
    description: initialData.description || '',
    due_at: initialData.due_at || '',
    status: initialData.status || 'pending' as TaskStatus,
  });

  const [dueDate, setDueDate] = useState(
    initialData.due_at ? new Date(initialData.due_at).toISOString().split('T')[0] : ''
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.title.trim()) {
      return;
    }

    const submitData = {
      ...formData,
      due_at: dueDate ? new Date(dueDate).toISOString() : undefined,
    };

    onSubmit(submitData);
  };


  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="title">כותרת המשימה *</Label>
        <Input
          id="title"
          value={formData.title}
          onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
          placeholder="הזן כותרת למשימה"
          required
          disabled={isLoading}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">תיאור</Label>
        <Textarea
          id="description"
          value={formData.description}
          onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
          placeholder="הזן תיאור מפורט למשימה"
          rows={3}
          disabled={isLoading}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="due_at">תאריך יעד</Label>
        <Input
          id="due_at"
          type="date"
          value={dueDate}
          onChange={(e) => setDueDate(e.target.value)}
          disabled={isLoading}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="status">סטטוס</Label>
        <Select
          value={formData.status}
          onValueChange={(value: TaskStatus) => 
            setFormData(prev => ({ ...prev, status: value }))
          }
          disabled={isLoading}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {statusOptions.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="flex justify-end gap-2 pt-4">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={isLoading}
        >
          ביטול
        </Button>
        <Button type="submit" disabled={isLoading || !formData.title.trim()}>
          {isLoading ? 'שומר...' : 'שמור'}
        </Button>
      </div>
    </form>
  );
}
