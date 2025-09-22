'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/Badge';
import { X, Plus } from 'lucide-react';
import { Contact, CreateContactData } from '@/lib/api/crm';
import { ButtonLoader } from '@/components/ui/page-loader';
import { AssetSelector } from './asset-selector';
import type { Asset } from '@/lib/normalizers/asset';

interface ContactFormProps {
  initialData?: Partial<Contact>;
  onSubmit: (data: CreateContactData & { selectedAsset?: Asset | null }) => Promise<void>;
  onCancel?: () => void;
  isLoading?: boolean;
}

export function ContactForm({ 
  initialData, 
  onSubmit, 
  onCancel, 
  isLoading = false 
}: ContactFormProps) {
  const [formData, setFormData] = useState<CreateContactData>({
    name: initialData?.name || '',
    phone: initialData?.phone || '',
    email: initialData?.email || '',
    equity: initialData?.equity ?? null,
    tags: initialData?.tags || [],
  });
  const [newTag, setNewTag] = useState('');
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) return;
    
    // Track form submission
    console.log('Contact form submitted:', {
      has_email: !!formData.email,
      has_phone: !!formData.phone,
      tags_count: formData.tags?.length || 0,
      is_edit: !!initialData?.id,
      has_selected_asset: !!selectedAsset,
      has_equity: typeof formData.equity === 'number',
    });
    
    await onSubmit({ ...formData, selectedAsset });
  };

  const addTag = () => {
    if (newTag.trim() && !formData.tags?.includes(newTag.trim())) {
      setFormData(prev => ({
        ...prev,
        tags: [...(prev.tags || []), newTag.trim()]
      }));
      setNewTag('');
    }
  };

  const removeTag = (tagToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      tags: (prev.tags || []).filter(tag => tag !== tagToRemove)
    }));
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addTag();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="name">שם מלא *</Label>
        <Input
          id="name"
          value={formData.name}
          onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
          placeholder="הזן שם מלא"
          required
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
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="email">אימייל</Label>
        <Input
          id="email"
          type="email"
          value={formData.email}
          onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
          placeholder="example@email.com"
        />
      </div>

      <AssetSelector
        selectedAssetId={selectedAsset?.id}
        onAssetSelect={setSelectedAsset}
        placeholder="בחר נכס שהלקוח מתעניין בו"
      />

      <div className="space-y-2">
        <Label htmlFor="equity">הון עצמי (אופציונלי)</Label>
        <Input
          id="equity"
          type="number"
          min={0}
          step={1000}
          value={formData.equity ?? ''}
          onChange={(e) => {
            const value = e.target.value;
            setFormData(prev => ({
              ...prev,
              equity: value === '' ? null : Number(value)
            }));
          }}
          placeholder="לדוגמה: 350000"
        />
        <p className="text-xs text-muted-foreground">
          המידע יסייע להפיק דוח משכנתא מותאם אישית
        </p>
      </div>

      <div className="space-y-2">
        <Label>תגיות</Label>
        <div className="flex gap-2">
          <Input
            value={newTag}
            onChange={(e) => setNewTag(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="הוסף תגית"
          />
          <Button type="button" onClick={addTag} size="sm">
            <Plus className="h-4 w-4" />
          </Button>
        </div>
        {(formData.tags?.length || 0) > 0 && (
          <div className="flex flex-wrap gap-2">
            {(formData.tags || []).map((tag) => (
              <Badge key={tag} variant="secondary" className="flex items-center gap-1">
                {tag}
                <button
                  type="button"
                  onClick={() => removeTag(tag)}
                  className="ml-1 hover:text-destructive"
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
          </div>
        )}
      </div>

      <div className="flex gap-2 pt-4">
        <Button type="submit" disabled={isLoading || !formData.name.trim()}>
          {isLoading ? (
            <>
              <ButtonLoader size="sm" />
              <span className="mr-2">שומר...</span>
            </>
          ) : (
            'שמור'
          )}
        </Button>
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel}>
            ביטול
          </Button>
        )}
      </div>
    </form>
  );
}
