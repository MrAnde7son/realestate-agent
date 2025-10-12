'use client';

import DashboardLayout from '@/components/layout/dashboard-layout';
import ContactsList from '@/components/crm/ContactsList';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';

export default function ContactsPage() {
  return (
    <DashboardLayout>
      <div className="container mx-auto p-3 sm:p-6 space-y-6">
        <Breadcrumb>
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

        <ContactsList />
      </div>
    </DashboardLayout>
  );
}
