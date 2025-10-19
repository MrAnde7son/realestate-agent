'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface User {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  company?: string;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  is_demo: boolean;
  is_staff: boolean;
  language?: string;
  timezone?: string;
  currency?: string;
  date_format?: string;
  notify_email: boolean;
  notify_whatsapp: boolean;
  notify_urgent: boolean;
  notification_time?: string;
}

interface UserFormProps {
  user?: User;
  onSubmit: (data: Partial<User> & { password?: string }) => Promise<void>;
  onCancel: () => void;
}

export function UserForm({ user, onSubmit, onCancel }: UserFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const isEditing = !!user;

  const [formData, setFormData] = useState({
    username: user?.username || '',
    email: user?.email || '',
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    phone: user?.phone || '',
    company: user?.company || '',
    role: user?.role && user.role.trim() ? user.role : 'private',
    is_active: user?.is_active ?? true,
    is_verified: user?.is_verified ?? false,
    is_demo: user?.is_demo ?? false,
    is_staff: user?.is_staff ?? false,
    password: '',
    confirm_password: '',
    language: user?.language && user.language.trim() ? user.language : 'he',
    timezone: user?.timezone && user.timezone.trim() ? user.timezone : 'Asia/Jerusalem',
    currency: user?.currency && user.currency.trim() ? user.currency : 'ils',
    date_format: user?.date_format || 'dd/mm/yyyy',
    notify_email: user?.notify_email ?? true,
    notify_whatsapp: user?.notify_whatsapp ?? false,
    notify_urgent: user?.notify_urgent ?? true,
    notification_time: user?.notification_time || '09:00',
  });

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.username.trim()) {
      newErrors.username = 'שם משתמש הוא שדה חובה';
    } else if (formData.username.length < 3) {
      newErrors.username = 'שם משתמש חייב להכיל לפחות 3 תווים';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'כתובת אימייל היא שדה חובה';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'כתובת אימייל לא תקינה';
    }

    if (formData.password && formData.password.length < 8) {
      newErrors.password = 'סיסמה חייבת להכיל לפחות 8 תווים';
    }

    if (formData.password && formData.password !== formData.confirm_password) {
      newErrors.confirm_password = 'הסיסמאות אינן תואמות';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    try {
      const submitData: Partial<User> & { password?: string } = {
        username: formData.username,
        email: formData.email,
        first_name: formData.first_name,
        last_name: formData.last_name,
        phone: formData.phone,
        company: formData.company,
        role: formData.role,
        is_active: formData.is_active,
        is_verified: formData.is_verified,
        is_demo: formData.is_demo,
        is_staff: formData.is_staff,
        language: formData.language,
        timezone: formData.timezone,
        currency: formData.currency,
        date_format: formData.date_format,
        notify_email: formData.notify_email,
        notify_whatsapp: formData.notify_whatsapp,
        notify_urgent: formData.notify_urgent,
        notification_time: formData.notification_time,
      };

      // Only include password if it's provided
      if (formData.password) {
        submitData.password = formData.password;
      }

      await onSubmit(submitData);
    } finally {
      setIsSubmitting(false);
    }
  };

  const roleOptions = [
    { value: 'admin', label: 'מנהל' },
    { value: 'broker', label: 'מתווך' },
    { value: 'appraiser', label: 'שמאי' },
    { value: 'investor', label: 'משקיע' },
    { value: 'viewer', label: 'צופה' },
    { value: 'private', label: 'פרטי' },
  ];

  const languageOptions = [
    { value: 'he', label: 'עברית' },
    { value: 'en', label: 'English' },
  ];

  const currencyOptions = [
    { value: 'ils', label: '₪ שקל' },
    { value: 'usd', label: '$ דולר' },
    { value: 'eur', label: '€ אירו' },
  ];

  const timezoneOptions = [
    { value: 'Asia/Jerusalem', label: 'ירושלים' },
    { value: 'UTC', label: 'UTC' },
    { value: 'America/New_York', label: 'ניו יורק' },
    { value: 'Europe/London', label: 'לונדון' },
  ];

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-4">
        <h3 className="text-lg font-medium">פרטי משתמש</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="username">שם משתמש *</Label>
            <Input
              id="username"
              value={formData.username}
              onChange={(e) => setFormData(prev => ({ ...prev, username: e.target.value }))}
              placeholder="הזן שם משתמש"
              required
              disabled={isSubmitting}
            />
            {errors.username && <p className="text-sm text-red-500">{errors.username}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">אימייל *</Label>
            <Input
              id="email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
              placeholder="example@email.com"
              required
              disabled={isSubmitting}
            />
            {errors.email && <p className="text-sm text-red-500">{errors.email}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="first_name">שם פרטי</Label>
            <Input
              id="first_name"
              value={formData.first_name}
              onChange={(e) => setFormData(prev => ({ ...prev, first_name: e.target.value }))}
              placeholder="הזן שם פרטי"
              disabled={isSubmitting}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="last_name">שם משפחה</Label>
            <Input
              id="last_name"
              value={formData.last_name}
              onChange={(e) => setFormData(prev => ({ ...prev, last_name: e.target.value }))}
              placeholder="הזן שם משפחה"
              disabled={isSubmitting}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="phone">טלפון</Label>
          <Input
            id="phone"
            type="tel"
            value={formData.phone}
            onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
            placeholder="050-1234567"
            disabled={isSubmitting}
            dir="ltr"
            inputMode="tel"
            className="text-left"
          />
          </div>

          <div className="space-y-2">
            <Label htmlFor="company">חברה</Label>
            <Input
              id="company"
              value={formData.company}
              onChange={(e) => setFormData(prev => ({ ...prev, company: e.target.value }))}
              placeholder="הזן שם חברה"
              disabled={isSubmitting}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="role">תפקיד</Label>
            <Select
              value={formData.role}
              onValueChange={(value) => setFormData(prev => ({ ...prev, role: value }))}
              disabled={isSubmitting}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {roleOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {/* Status Section */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium">סטטוס משתמש</h3>
        <div className="space-y-3">
          <div className="flex items-center space-x-3 rtl:space-x-reverse">
            <input
              type="checkbox"
              id="is_active"
              checked={formData.is_active}
              onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
              className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
              disabled={isSubmitting}
            />
            <Label htmlFor="is_active">משתמש פעיל</Label>
          </div>
          
          <div className="flex items-center space-x-3 rtl:space-x-reverse">
            <input
              type="checkbox"
              id="is_verified"
              checked={formData.is_verified}
              onChange={(e) => setFormData(prev => ({ ...prev, is_verified: e.target.checked }))}
              className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
              disabled={isSubmitting}
            />
            <Label htmlFor="is_verified">משתמש מאומת</Label>
          </div>
          
          <div className="flex items-center space-x-3 rtl:space-x-reverse">
            <input
              type="checkbox"
              id="is_demo"
              checked={formData.is_demo}
              onChange={(e) => setFormData(prev => ({ ...prev, is_demo: e.target.checked }))}
              className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
              disabled={isSubmitting}
            />
            <Label htmlFor="is_demo">משתמש דמו</Label>
          </div>
          
          <div className="flex items-center space-x-3 rtl:space-x-reverse">
            <input
              type="checkbox"
              id="is_staff"
              checked={formData.is_staff}
              onChange={(e) => setFormData(prev => ({ ...prev, is_staff: e.target.checked }))}
              className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
              disabled={isSubmitting}
            />
            <Label htmlFor="is_staff">צוות</Label>
          </div>
        </div>
      </div>

      {/* Password Section */}
      {!isEditing && (
        <div className="space-y-4">
          <h3 className="text-lg font-medium">סיסמה</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="password">סיסמה *</Label>
              <Input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                placeholder="הזן סיסמה"
                required
                disabled={isSubmitting}
              />
              {errors.password && <p className="text-sm text-red-500">{errors.password}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirm_password">אישור סיסמה *</Label>
              <Input
                id="confirm_password"
                type="password"
                value={formData.confirm_password}
                onChange={(e) => setFormData(prev => ({ ...prev, confirm_password: e.target.value }))}
                placeholder="הזן סיסמה שוב"
                required
                disabled={isSubmitting}
              />
              {errors.confirm_password && <p className="text-sm text-red-500">{errors.confirm_password}</p>}
            </div>
          </div>
        </div>
      )}

      {/* Settings Section */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium">הגדרות</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="language">שפה</Label>
            <Select
              value={formData.language}
              onValueChange={(value) => setFormData(prev => ({ ...prev, language: value }))}
              disabled={isSubmitting}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {languageOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="timezone">אזור זמן</Label>
            <Select
              value={formData.timezone}
              onValueChange={(value) => setFormData(prev => ({ ...prev, timezone: value }))}
              disabled={isSubmitting}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {timezoneOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="currency">מטבע</Label>
            <Select
              value={formData.currency}
              onValueChange={(value) => setFormData(prev => ({ ...prev, currency: value }))}
              disabled={isSubmitting}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {currencyOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="date_format">פורמט תאריך</Label>
            <Input
              id="date_format"
              value={formData.date_format}
              onChange={(e) => setFormData(prev => ({ ...prev, date_format: e.target.value }))}
              placeholder="dd/mm/yyyy"
              disabled={isSubmitting}
            />
          </div>
        </div>
      </div>

      {/* Notifications */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium">התראות</h3>
        <div className="space-y-3">
          <div className="flex items-center space-x-3 rtl:space-x-reverse">
            <input
              type="checkbox"
              id="notify_email"
              checked={formData.notify_email}
              onChange={(e) => setFormData(prev => ({ ...prev, notify_email: e.target.checked }))}
              className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
              disabled={isSubmitting}
            />
            <Label htmlFor="notify_email">התראות באימייל</Label>
          </div>
          
          <div className="flex items-center space-x-3 rtl:space-x-reverse">
            <input
              type="checkbox"
              id="notify_whatsapp"
              checked={formData.notify_whatsapp}
              onChange={(e) => setFormData(prev => ({ ...prev, notify_whatsapp: e.target.checked }))}
              className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
              disabled={isSubmitting}
            />
            <Label htmlFor="notify_whatsapp">התראות בווטסאפ</Label>
          </div>
          
          <div className="flex items-center space-x-3 rtl:space-x-reverse">
            <input
              type="checkbox"
              id="notify_urgent"
              checked={formData.notify_urgent}
              onChange={(e) => setFormData(prev => ({ ...prev, notify_urgent: e.target.checked }))}
              className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
              disabled={isSubmitting}
            />
            <Label htmlFor="notify_urgent">התראות דחופות</Label>
          </div>
        </div>
        
        <div className="space-y-2">
          <Label htmlFor="notification_time">שעת התראות</Label>
          <Input
            id="notification_time"
            type="time"
            value={formData.notification_time}
            onChange={(e) => setFormData(prev => ({ ...prev, notification_time: e.target.value }))}
            disabled={isSubmitting}
          />
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-3 pt-6">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={isSubmitting}
        >
          ביטול
        </Button>
        <Button
          type="submit"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'שומר...' : (isEditing ? 'עדכן משתמש' : 'צור משתמש')}
        </Button>
      </div>
    </form>
  );
}