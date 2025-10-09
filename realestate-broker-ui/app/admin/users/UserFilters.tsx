'use client';

import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/Badge';
import { Filter, X } from 'lucide-react';

interface UserFiltersProps {
  roleFilter: string;
  statusFilter: string;
  onRoleFilter: (value: string) => void;
  onStatusFilter: (value: string) => void;
  onClearFilters: () => void;
}

const ROLE_OPTIONS = [
  { value: 'all', label: 'כל התפקידים' },
  { value: 'admin', label: 'מנהל' },
  { value: 'broker', label: 'מתווך' },
  { value: 'appraiser', label: 'שמאי' },
  { value: 'investor', label: 'משקיע' },
  { value: 'viewer', label: 'צופה' },
  { value: 'private', label: 'פרטי' },
];

const STATUS_OPTIONS = [
  { value: 'all', label: 'כל הסטטוסים' },
  { value: 'active', label: 'פעיל' },
  { value: 'inactive', label: 'לא פעיל' },
];

export function UserFilters({
  roleFilter,
  statusFilter,
  onRoleFilter,
  onStatusFilter,
  onClearFilters,
}: UserFiltersProps) {
  const hasActiveFilters = roleFilter !== 'all' || statusFilter !== 'all';

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" size="sm" className="min-h-[44px]">
          <Filter className="h-4 w-4 me-2" />
          <span className="hidden sm:inline">סינון</span>
          {hasActiveFilters && (
            <Badge variant="secondary" className="mr-2 h-5 w-5 p-0 flex items-center justify-center text-xs">
              !
            </Badge>
          )}
        </Button>
      </SheetTrigger>
      <SheetContent className="w-80" side="right">
        <SheetHeader>
          <SheetTitle>סינון משתמשים</SheetTitle>
        </SheetHeader>
        <div className="space-y-3 max-h-[calc(100vh-120px)] overflow-y-auto pr-2">
          <div className="flex items-center justify-between">
            {hasActiveFilters && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onClearFilters}
                className="h-8 px-2"
              >
                <X className="h-3 w-3 me-1" />
                נקה הכל
              </Button>
            )}
          </div>

          <div className="grid grid-cols-1 gap-3">
            {/* Role filter */}
            <div className="space-y-1">
              <Label htmlFor="role-filter" className="text-sm">תפקיד</Label>
              <Select value={roleFilter} onValueChange={onRoleFilter}>
                <SelectTrigger id="role-filter">
                  <SelectValue placeholder="בחר תפקיד" />
                </SelectTrigger>
                <SelectContent>
                  {ROLE_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            {/* Status filter */}
            <div className="space-y-1">
              <Label htmlFor="status-filter" className="text-sm">סטטוס</Label>
              <Select value={statusFilter} onValueChange={onStatusFilter}>
                <SelectTrigger id="status-filter">
                  <SelectValue placeholder="בחר סטטוס" />
                </SelectTrigger>
                <SelectContent>
                  {STATUS_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
