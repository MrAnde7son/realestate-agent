'use client';

import DashboardLayout from '@/components/layout/dashboard-layout';
import LeadsList from '@/components/crm/LeadsList';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';

export default function LeadsPage() {
  return (
    <DashboardLayout>
      <div className="w-full p-3 sm:p-6 space-y-6 px-4 sm:px-6 lg:px-8">
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink href="/crm">לקוחות ולידים</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbPage>לידים</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>

        <LeadsList />
      </div>
    </DashboardLayout>
  );
}
