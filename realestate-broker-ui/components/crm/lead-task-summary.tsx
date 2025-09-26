'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/button';
import { CheckSquare, Clock, AlertCircle } from 'lucide-react';
import { Lead, ContactTask, CrmApi } from '@/lib/api/crm';

interface LeadTaskSummaryProps {
  lead: Lead;
  onShowTasks?: () => void;
  compact?: boolean;
}

// Simple cache to avoid multiple API calls for the same lead
const taskCache = new Map<number, { tasks: ContactTask[]; timestamp: number }>();
const CACHE_DURATION = 30000; // 30 seconds

// Function to clear cache for a specific lead (useful when tasks are updated)
export const clearTaskCache = (leadId: number) => {
  taskCache.delete(leadId);
};

export function LeadTaskSummary({ lead, onShowTasks, compact = true }: LeadTaskSummaryProps) {
  const [tasks, setTasks] = useState<ContactTask[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const hasLoadedRef = useRef(false);

  const loadTasks = useCallback(async () => {
    // Check cache first
    const cached = taskCache.get(lead.id);
    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
      setTasks(cached.tasks);
      return;
    }

    try {
      setIsLoading(true);
      const data = await CrmApi.getLeadTasks(lead.id);
      setTasks(data);
      // Cache the result
      taskCache.set(lead.id, { tasks: data, timestamp: Date.now() });
    } catch (error) {
      // Silently fail for summary - don't show toast for every lead
      console.error('Failed to load tasks for lead:', lead.id);
    } finally {
      setIsLoading(false);
    }
  }, [lead.id]);

  useEffect(() => {
    if (!hasLoadedRef.current) {
      hasLoadedRef.current = true;
      loadTasks();
    }
  }, [lead.id, loadTasks]);

  const pendingTasks = tasks.filter(task => task.status === 'pending');
  const overdueTasks = pendingTasks.filter(task => {
    if (!task.due_at) return false;
    return new Date(task.due_at) < new Date();
  });

  if (isLoading) {
    return (
      <div className="flex items-center gap-1">
        <div className="w-4 h-4 bg-gray-200 rounded animate-pulse" />
        {!compact && <span className="text-sm text-muted-foreground">טוען...</span>}
      </div>
    );
  }

  if (tasks.length === 0) {
    return null; // Don't show anything if no tasks
  }

  if (compact) {
    return (
      <div className="flex items-center gap-1">
        {overdueTasks.length > 0 && (
          <Badge variant="destructive" className="text-xs px-1 py-0">
            <AlertCircle className="h-2 w-2 sm:h-3 sm:w-3 mr-1" />
            {overdueTasks.length}
          </Badge>
        )}
        {pendingTasks.length > 0 && overdueTasks.length === 0 && (
          <Badge variant="secondary" className="text-xs px-1 py-0">
            <Clock className="h-2 w-2 sm:h-3 sm:w-3 mr-1" />
            {pendingTasks.length}
          </Badge>
        )}
        {onShowTasks && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onShowTasks}
            className="h-5 w-5 sm:h-6 sm:w-6 p-0"
            title="ניהול משימות"
          >
            <CheckSquare className="h-2 w-2 sm:h-3 sm:w-3" />
          </Button>
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2">
      <div className="flex items-center gap-1 flex-wrap">
        {overdueTasks.length > 0 && (
          <Badge variant="destructive" className="text-xs">
            <AlertCircle className="h-2 w-2 sm:h-3 sm:w-3 mr-1" />
            <span className="hidden sm:inline">{overdueTasks.length} משימות באיחור</span>
            <span className="sm:hidden">{overdueTasks.length}</span>
          </Badge>
        )}
        {pendingTasks.length > 0 && overdueTasks.length === 0 && (
          <Badge variant="secondary" className="text-xs">
            <Clock className="h-2 w-2 sm:h-3 sm:w-3 mr-1" />
            <span className="hidden sm:inline">{pendingTasks.length} משימות ממתינות</span>
            <span className="sm:hidden">{pendingTasks.length}</span>
          </Badge>
        )}
        {tasks.length > pendingTasks.length && (
          <Badge variant="outline" className="text-xs">
            <CheckSquare className="h-2 w-2 sm:h-3 sm:w-3 mr-1" />
            <span className="hidden sm:inline">{tasks.length - pendingTasks.length} הושלמו</span>
            <span className="sm:hidden">{tasks.length - pendingTasks.length}</span>
          </Badge>
        )}
      </div>
      {onShowTasks && (
        <Button
          variant="outline"
          size="sm"
          onClick={onShowTasks}
          className="h-7 w-7 p-0"
          title="ניהול משימות"
        >
          <CheckSquare className="h-3 w-3" />
        </Button>
      )}
    </div>
  );
}
