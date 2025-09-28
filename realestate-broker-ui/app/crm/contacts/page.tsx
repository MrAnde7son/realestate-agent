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
import { Plus, Search, Edit, Trash2 } from 'lucide-react';
import { Contact, CrmApi, CreateContactData } from '@/lib/api/crm';
import { ContactForm } from '@/components/crm/contact-form';
import { useToast } from '@/hooks/use-toast';
import DashboardLayout from '@/components/layout/dashboard-layout';
import { PageLoader } from '@/components/ui/page-loader';
import { Skeleton } from '@/components/ui/skeleton';
import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from '@/components/ui/breadcrumb';

export default function ContactsPage() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [editingContact, setEditingContact] = useState<Contact | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();

  const formatEquity = (value: number | null) => {
    if (value === null || Number.isNaN(value)) {
      return '-';
    }

    return new Intl.NumberFormat('he-IL', {
      style: 'currency',
      currency: 'ILS',
      maximumFractionDigits: 0
    }).format(value);
  };

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

  const handleCreateContact = async (data: CreateContactData & { selectedAsset?: any }) => {
    try {
      setIsSubmitting(true);
      const contact = await CrmApi.createContact(data);
      
      // If an asset was selected, create a lead automatically
      if (data.selectedAsset) {
        try {
          await CrmApi.createLead({
            contact_id_write: contact.id,
            asset_id: data.selectedAsset.id,
            status: 'new'
          });
          
          toast({
            title: 'לקוח וליד נוצרו',
            description: `הלקוח נוצר בהצלחה וליד חדש נוצר עבור הנכס ${data.selectedAsset.address}.`,
          });
        } catch (leadError: any) {
          console.error('Error creating lead:', leadError);
          toast({
            title: 'לקוח נוצר, שגיאה בליד',
            description: 'הלקוח נוצר בהצלחה אך לא ניתן ליצור ליד עבור הנכס שנבחר.',
            variant: 'destructive',
          });
        }
      } else {
        toast({
          title: 'לקוח נוצר',
          description: 'הלקוח החדש נוצר בהצלחה.',
        });
      }
      
      setIsCreateDialogOpen(false);
      loadContacts();
    } catch (error: any) {
      toast({
        title: 'שגיאה',
        description: error.message || 'לא ניתן ליצור לקוח חדש.',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateContact = async (data: CreateContactData & { selectedAsset?: any }) => {
    if (!editingContact) return;

    try {
      setIsSubmitting(true);
      await CrmApi.updateContact(editingContact.id, data);
      
      // If an asset was selected, create a lead automatically
      if (data.selectedAsset) {
        try {
          await CrmApi.createLead({
            contact_id_write: editingContact.id,
            asset_id: data.selectedAsset.id,
            status: 'new'
          });
          
          toast({
            title: 'לקוח עודכן וליד נוצר',
            description: `הלקוח עודכן בהצלחה וליד חדש נוצר עבור הנכס ${data.selectedAsset.address}.`,
          });
        } catch (leadError: any) {
          console.error('Error creating lead:', leadError);
          toast({
            title: 'לקוח עודכן, שגיאה בליד',
            description: 'הלקוח עודכן בהצלחה אך לא ניתן ליצור ליד עבור הנכס שנבחר.',
            variant: 'destructive',
          });
        }
      } else {
        toast({
          title: 'לקוח עודכן',
          description: 'הלקוח עודכן בהצלחה',
        });
      }
      
      setEditingContact(null);
      loadContacts();
    } catch (error: any) {
      toast({
        title: 'שגיאה',
        description: error.message || 'לא ניתן לעדכן את הלקוח',
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

  const filteredContacts = contacts.filter(contact => {
    const normalizedQuery = searchQuery.toLowerCase();
    const equityQuery = contact.equity !== null ? contact.equity.toString() : '';

    return (
      contact.name.toLowerCase().includes(normalizedQuery) ||
      (contact.email || '').toLowerCase().includes(normalizedQuery) ||
      (contact.phone || '').includes(searchQuery) ||
      contact.tags.some(tag => tag.toLowerCase().includes(normalizedQuery)) ||
      equityQuery.includes(searchQuery)
    );
  });

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
        <Breadcrumb className="mb-6">
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink href="/crm">לקוחות ולידים</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbPage>לקוחות</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
        
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
                <TableHead>הון עצמי</TableHead>
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
                  <TableCell>{formatEquity(contact.equity)}</TableCell>
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
