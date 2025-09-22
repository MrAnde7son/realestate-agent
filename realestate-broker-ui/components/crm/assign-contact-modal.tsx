'use client';

import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogTrigger 
} from '@/components/ui/dialog';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Contact, CrmApi, CreateContactData, CreateLeadData } from '@/lib/api/crm';
import { ContactForm } from './contact-form';
import { useToast } from '@/hooks/use-toast';

interface AssignContactModalProps {
  assetId: number;
  assetAddress?: string;
  onCreated: () => void;
  trigger?: React.ReactNode;
}

export function AssignContactModal({ 
  assetId, 
  assetAddress, 
  onCreated, 
  trigger 
}: AssignContactModalProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [selectedContactId, setSelectedContactId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [isCreatingContact, setIsCreatingContact] = useState(false);
  const { toast } = useToast();

  const loadContacts = useCallback(async () => {
    try {
      const data = await CrmApi.getContacts();
      setContacts(data);
    } catch (error) {
      toast({
        title: 'שגיאה',
        description: 'לא ניתן לטעון את רשימת הלקוחות',
        variant: 'destructive',
      });
    }
  }, [toast]);

  useEffect(() => {
    if (isOpen) {
      loadContacts();
    }
  }, [isOpen, loadContacts]);

  const handleAssignExistingContact = async () => {
    if (!selectedContactId) return;

    try {
      setIsLoading(true);
      await CrmApi.createLead({
        contact_id: parseInt(selectedContactId),
        asset_id: assetId,
        status: 'new'
      });
      
      onCreated();
      setIsOpen(false);
      setSelectedContactId('');
      
      toast({
        title: 'לקוח שויך',
        description: 'הלקוח שויך לנכס בהצלחה',
      });
    } catch (error) {
      toast({
        title: 'שגיאה',
        description: 'לא ניתן לשייך את הלקוח',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateAndAssignContact = async (contactData: CreateContactData) => {
    try {
      setIsCreatingContact(true);
      
      // Create contact
      const newContact = await CrmApi.createContact(contactData);
      
      // Create lead
      await CrmApi.createLead({
        contact_id: newContact.id,
        asset_id: assetId,
        status: 'new'
      });
      
      onCreated();
      setIsOpen(false);
      
      toast({
        title: 'לקוח נוצר ושויך',
        description: 'הלקוח נוצר ושויך לנכס בהצלחה',
      });
    } catch (error) {
      toast({
        title: 'שגיאה',
        description: 'לא ניתן ליצור ולשייך את הלקוח',
        variant: 'destructive',
      });
    } finally {
      setIsCreatingContact(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button>
            שייך לקוח
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            שיוך לקוח לנכס
            {assetAddress && (
              <div className="text-sm font-normal text-muted-foreground mt-1">
                {assetAddress}
              </div>
            )}
          </DialogTitle>
        </DialogHeader>

        <Tabs defaultValue="existing" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="existing">לקוח קיים</TabsTrigger>
            <TabsTrigger value="new">לקוח חדש</TabsTrigger>
          </TabsList>

          <TabsContent value="existing" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="contact-select">בחר לקוח</Label>
              <Select value={selectedContactId} onValueChange={setSelectedContactId}>
                <SelectTrigger>
                  <SelectValue placeholder="בחר לקוח מהרשימה" />
                </SelectTrigger>
                <SelectContent>
                  {contacts.map((contact) => (
                    <SelectItem key={contact.id} value={contact.id.toString()}>
                      <div className="flex flex-col">
                        <span className="font-medium">{contact.name}</span>
                        {contact.email && (
                          <span className="text-sm text-muted-foreground">
                            {contact.email}
                          </span>
                        )}
                        {contact.phone && (
                          <span className="text-sm text-muted-foreground">
                            {contact.phone}
                          </span>
                        )}
                        {contact.equity !== null && (
                          <span className="text-sm text-muted-foreground">
                            הון עצמי: {new Intl.NumberFormat('he-IL', {
                              style: 'currency',
                              currency: 'ILS',
                              maximumFractionDigits: 0
                            }).format(contact.equity)}
                          </span>
                        )}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Button 
              onClick={handleAssignExistingContact}
              disabled={!selectedContactId || isLoading}
              className="w-full"
            >
              {isLoading ? 'משייך...' : 'שייך לקוח'}
            </Button>
          </TabsContent>

          <TabsContent value="new" className="space-y-4">
            <ContactForm
              onSubmit={handleCreateAndAssignContact}
              isLoading={isCreatingContact}
            />
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
