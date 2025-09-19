'use client';

import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
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
import { Badge } from '@/components/ui/Badge';
import { Plus, Search, Edit, Trash2, Eye } from 'lucide-react';
import { Contact, CrmApi, CreateContactData } from '@/lib/api/crm';
import { ContactForm } from '@/components/crm/contact-form';
import { useToast } from '@/hooks/use-toast';
import DashboardLayout from '@/components/layout/dashboard-layout';
import { PageLoader } from '@/components/ui/page-loader';
import { Skeleton } from '@/components/ui/skeleton';

export default function ContactsPage() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [editingContact, setEditingContact] = useState<Contact | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();

  const loadContacts = useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await CrmApi.getContacts();
      setContacts(data);
    } catch (error) {
      toast({
        title: 'שגיאה',
        description: 'לא ניתן לטעון את רשימת הלקוחות',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    loadContacts();
  }, [loadContacts]);

  const handleCreateContact = async (data: CreateContactData) => {
    try {
      setIsSubmitting(true);
      await CrmApi.createContact(data);
      await loadContacts();
      setIsCreateDialogOpen(false);
      toast({
        title: 'לקוח נוצר',
        description: 'הלקוח נוצר בהצלחה',
      });
    } catch (error) {
      toast({
        title: 'שגיאה',
        description: 'לא ניתן ליצור את הלקוח',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateContact = async (data: CreateContactData) => {
    if (!editingContact) return;

    try {
      setIsSubmitting(true);
      await CrmApi.updateContact(editingContact.id, data);
      await loadContacts();
      setEditingContact(null);
      toast({
        title: 'לקוח עודכן',
        description: 'הלקוח עודכן בהצלחה',
      });
    } catch (error) {
      toast({
        title: 'שגיאה',
        description: 'לא ניתן לעדכן את הלקוח',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteContact = async (contact: Contact) => {
    if (!confirm(`האם אתה בטוח שברצונך למחוק את ${contact.name}?`)) {
      return;
    }

    try {
      await CrmApi.deleteContact(contact.id);
      await loadContacts();
      toast({
        title: 'לקוח נמחק',
        description: 'הלקוח נמחק בהצלחה',
      });
    } catch (error) {
      toast({
        title: 'שגיאה',
        description: 'לא ניתן למחוק את הלקוח',
        variant: 'destructive',
      });
    }
  };

  const filteredContacts = contacts.filter(contact =>
    contact.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    contact.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    contact.phone.includes(searchQuery)
  );

  if (isLoading) {
    return (
      <DashboardLayout>
        <PageLoader message="טוען לקוחות..." showLogo={false} />
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">לקוחות</h1>
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              לקוח חדש
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>יצירת לקוח חדש</DialogTitle>
            </DialogHeader>
            <ContactForm
              onSubmit={handleCreateContact}
              isLoading={isSubmitting}
              onCancel={() => setIsCreateDialogOpen(false)}
            />
          </DialogContent>
        </Dialog>
      </div>

      <div className="mb-6">
        <div className="relative">
          <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <Input
            placeholder="חפש לקוחות..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pr-10"
          />
        </div>
      </div>

      {filteredContacts.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-lg text-muted-foreground mb-4">
            {searchQuery ? 'לא נמצאו לקוחות התואמים לחיפוש' : 'אין עדיין לקוחות'}
          </div>
          {!searchQuery && (
            <Button onClick={() => setIsCreateDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              צור לקוח ראשון
            </Button>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>שם</TableHead>
                <TableHead>אימייל</TableHead>
                <TableHead>טלפון</TableHead>
                <TableHead>תגיות</TableHead>
                <TableHead>נוצר</TableHead>
                <TableHead className="text-left">פעולות</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredContacts.map((contact) => (
                <TableRow key={contact.id}>
                  <TableCell className="font-medium">{contact.name}</TableCell>
                  <TableCell>{contact.email || '-'}</TableCell>
                  <TableCell>{contact.phone || '-'}</TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {contact.tags.map((tag) => (
                        <Badge key={tag} variant="secondary" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell>
                    {new Date(contact.created_at).toLocaleDateString('he-IL')}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setEditingContact(contact)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDeleteContact(contact)}
                        className="text-destructive hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {/* Edit Contact Dialog */}
      <Dialog open={!!editingContact} onOpenChange={() => setEditingContact(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>עריכת לקוח</DialogTitle>
          </DialogHeader>
          {editingContact && (
            <ContactForm
              initialData={editingContact}
              onSubmit={handleUpdateContact}
              isLoading={isSubmitting}
              onCancel={() => setEditingContact(null)}
            />
          )}
        </DialogContent>
      </Dialog>
      </div>
    </DashboardLayout>
  );
}
