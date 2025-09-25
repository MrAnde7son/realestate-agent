'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogTrigger 
} from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { 
  MoreHorizontal, 
  MessageSquare, 
  Send, 
  Edit,
  Trash2,
  CheckSquare
} from 'lucide-react';
import { Lead, LeadStatus, CrmApi } from '@/lib/api/crm';
import { useToast } from '@/hooks/use-toast';
import { ButtonLoader } from '@/components/ui/page-loader';

interface LeadRowActionsProps {
  lead: Lead;
  onUpdate: () => void;
  onDelete: (leadId: number) => void;
}

const statusOptions: { value: LeadStatus; label: string }[] = [
  { value: 'new', label: 'חדש' },
  { value: 'contacted', label: 'יצרתי קשר' },
  { value: 'interested', label: 'מתעניין' },
  { value: 'negotiating', label: 'במשא ומתן' },
  { value: 'closed-won', label: 'נסגר בהצלחה' },
  { value: 'closed-lost', label: 'נסגר ללא הצלחה' },
];

export function LeadRowActions({ lead, onUpdate, onDelete }: LeadRowActionsProps) {
  const [isNoteDialogOpen, setIsNoteDialogOpen] = useState(false);
  const [noteText, setNoteText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const handleStatusChange = async (newStatus: LeadStatus) => {
    try {
      setIsLoading(true);
      await CrmApi.updateLeadStatus(lead.id, { status: newStatus });
      onUpdate();
      
      // Track status change
      console.log('Lead status changed:', {
        lead_id: lead.id,
        from_status: lead.status,
        to_status: newStatus,
        contact_name: lead.contact.name,
        asset_id: lead.asset_id
      });
      
      toast({
        title: 'סטטוס עודכן',
        description: 'הסטטוס עודכן בהצלחה',
      });
    } catch (error) {
      toast({
        title: 'שגיאה',
        description: 'לא ניתן לעדכן את הסטטוס',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddNote = async () => {
    if (!noteText.trim()) return;
    
    try {
      setIsLoading(true);
      await CrmApi.addLeadNote(lead.id, { text: noteText });
      setNoteText('');
      setIsNoteDialogOpen(false);
      onUpdate();
      
      // Track note addition
      console.log('Lead note added:', {
        lead_id: lead.id,
        note_length: noteText.length,
        status: lead.status,
        contact_name: lead.contact.name,
        asset_id: lead.asset_id
      });
      
      toast({
        title: 'הערה נוספה',
        description: 'ההערה נוספה בהצלחה',
      });
    } catch (error) {
      toast({
        title: 'שגיאה',
        description: 'לא ניתן להוסיף הערה',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendReport = async () => {
    try {
      setIsLoading(true);
      const result = await CrmApi.sendLeadReport(lead.id);
      
      // Track report sending
      console.log('Lead report sent:', {
        lead_id: lead.id,
        via: result.contact_email ? 'email' : 'link',
        contact_email: result.contact_email,
        status: lead.status,
        contact_name: lead.contact.name,
        asset_id: lead.asset_id
      });
      
      toast({
        title: 'דוח נשלח',
        description: `הדוח נשלח ל-${result.contact_email}`,
      });
    } catch (error) {
      toast({
        title: 'שגיאה',
        description: 'לא ניתן לשלוח דוח',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex items-center gap-1 sm:gap-2">
      {/* Status Change Dropdown */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm" disabled={isLoading} className="h-8 w-8 p-0">
            <Edit className="h-3 w-3" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-48">
          {statusOptions.map((option) => (
            <DropdownMenuItem
              key={option.value}
              onClick={() => handleStatusChange(option.value)}
              className={lead.status === option.value ? 'bg-blue-100 text-blue-900 font-medium' : ''}
            >
              {option.label}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Add Note Dialog */}
      <Dialog open={isNoteDialogOpen} onOpenChange={setIsNoteDialogOpen}>
        <DialogTrigger asChild>
          <Button variant="outline" size="sm" disabled={isLoading} className="h-8 w-8 p-0">
            <MessageSquare className="h-3 w-3" />
          </Button>
        </DialogTrigger>
        <DialogContent className="mx-4 sm:mx-0">
          <DialogHeader>
            <DialogTitle>הוסף הערה</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="note">הערה</Label>
              <Textarea
                id="note"
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                placeholder="הזן הערה..."
                rows={3}
              />
            </div>
            <div className="flex flex-col sm:flex-row gap-2">
              <Button onClick={handleAddNote} disabled={!noteText.trim() || isLoading} className="w-full sm:w-auto">
                {isLoading ? (
                  <>
                    <ButtonLoader size="sm" />
                    <span className="mr-2">מוסיף...</span>
                  </>
                ) : (
                  'הוסף'
                )}
              </Button>
              <Button variant="outline" onClick={() => setIsNoteDialogOpen(false)} className="w-full sm:w-auto">
                ביטול
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Send Report */}
      <Button 
        variant="outline" 
        size="sm" 
        onClick={handleSendReport}
        disabled={isLoading || !lead.contact.email}
        title={!lead.contact.email ? 'אין כתובת אימייל' : 'שלח דוח'}
        className="h-8 w-8 p-0"
      >
        {isLoading ? <ButtonLoader size="sm" /> : <Send className="h-3 w-3" />}
      </Button>

      {/* Delete */}
      <Button 
        variant="outline" 
        size="sm" 
        onClick={() => onDelete(lead.id)}
        disabled={isLoading}
        className="text-destructive hover:text-destructive h-8 w-8 p-0"
        title="מחק"
      >
        <Trash2 className="h-3 w-3" />
      </Button>
    </div>
  );
}
