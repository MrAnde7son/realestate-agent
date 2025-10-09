'use client';

import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';

interface UserFiltersProps {
  roleFilter: string;
  statusFilter: string;
  onRoleFilter: (value: string) => void;
  onStatusFilter: (value: string) => void;
}

const ROLE_OPTIONS = [
  { value: '', label: 'כל התפקידים' },
  { value: 'admin', label: 'מנהל' },
  { value: 'broker', label: 'מתווך' },
  { value: 'appraiser', label: 'שמאי' },
  { value: 'investor', label: 'משקיע' },
  { value: 'viewer', label: 'צופה' },
  { value: 'private', label: 'פרטי' },
];

const STATUS_OPTIONS = [
  { value: '', label: 'כל הסטטוסים' },
  { value: 'active', label: 'פעיל' },
  { value: 'inactive', label: 'לא פעיל' },
];

export function UserFilters({
  roleFilter,
  statusFilter,
  onRoleFilter,
  onStatusFilter,
}: UserFiltersProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t">
      <div className="space-y-2">
        <Label htmlFor="role-filter">תפקיד</Label>
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
      
      <div className="space-y-2">
        <Label htmlFor="status-filter">סטטוס</Label>
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
  );
}
