import DashboardLayout from '@/components/layout/dashboard-layout'
import { DashboardShell, DashboardHeader } from '@/components/layout/dashboard-shell'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function BillingPage() {
  return (
    <DashboardLayout>
      <DashboardShell>
        <DashboardHeader heading="חיוב" text="ניהול פרטי החיוב שלך" />
        <Card>
          <CardHeader>
            <CardTitle>תוכנית נוכחית</CardTitle>
          </CardHeader>
          <CardContent>
            בקרוב תצוגת חיוב...
          </CardContent>
        </Card>
      </DashboardShell>
    </DashboardLayout>
  )
}
