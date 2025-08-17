'use client'
import React from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, THead, TBody, TR, TH, TD } from '@/components/ui/table'
import { API_BASE } from '@/lib/config'
import DashboardLayout from '@/components/layout/dashboard-layout'

const schema = z.object({ 
  rule_name: z.string().min(1,'שם חוק נדרש'), 
  city: z.string().optional(), 
  max_price: z.coerce.number().optional(), 
  beds_min: z.coerce.number().optional(), 
  beds_max: z.coerce.number().optional(), 
  confidence_min: z.coerce.number().min(0).max(100).optional(), 
  risk: z.enum(['any','none']).default('any'), 
  remaining_rights_min: z.coerce.number().optional(), 
  notify_email: z.boolean().default(true), 
  notify_whatsapp: z.boolean().default(false) 
})

type FormData = z.infer<typeof schema>

export default function AlertsPage(){
  const { register, handleSubmit, formState: { errors, isSubmitting }, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { rule_name:'', risk:'any', notify_email:true, notify_whatsapp:false, confidence_min:70 }
  })
  const [alerts, setAlerts] = React.useState<any[]>([])

  React.useEffect(()=>{
    fetch(`${API_BASE}/api/alerts/`)
      .then(res=>res.json())
      .then(data=>setAlerts(data.rows||[]))
      .catch(()=>setAlerts([]))
  },[])
  
  async function onSubmit(values: FormData){
    const payload = { 
      user_id:'demo-user', 
      criteria:{ 
        city: values.city || undefined, 
        max_price: values.max_price || undefined, 
        beds:{ min: values.beds_min || undefined, max: values.beds_max || undefined }, 
        confidence_min: values.confidence_min || undefined, 
        risk: values.risk, 
        remaining_rights_min: values.remaining_rights_min || undefined 
      }, 
      notify:[ 
        ...(values.notify_email?['email']:[]), 
        ...(values.notify_whatsapp?['whatsapp']:[]) 
      ] 
    }
    const res = await fetch(`${API_BASE}/api/alerts/`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) })
    if(!res.ok){ const txt = await res.text(); alert('שמירה נכשלה: '+txt); return }
    const data = await res.json(); alert('נשמר ✓ (id: '+data.id+')'); reset()
  }
  
  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold">חוקי התראות</h1>
          <p className="text-muted-foreground">צרו התראות חכמות על בסיס תנאים מתקדמים</p>
        </div>

        {/* Form */}
        <Card>
          <CardHeader>
            <CardTitle>הגדרת התראה חדשה</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-sm font-medium">שם החוק</label>
                <Input {...register('rule_name')} placeholder="3–4 חד בת״א עד 8.5מיל ללא סיכון" />
                {errors.rule_name && <div className="text-destructive text-xs">{errors.rule_name.message}</div>}
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium">עיר</label>
                <Input {...register('city')} placeholder="תל אביב-יפו" />
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium">מחיר עד (₪)</label>
                <Input {...register('max_price')} placeholder="8500000" type="number" />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">חדרים מינ׳</label>
                  <Input {...register('beds_min')} placeholder="3" type="number" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">חדרים מקס׳</label>
                  <Input {...register('beds_max')} placeholder="4" type="number" />
                </div>
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium">Confidence מינ׳ (%)</label>
                <Input {...register('confidence_min')} placeholder="70" type="number" />
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium">סיכון</label>
                <select {...register('risk')} className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background">
                  <option value="any">הכל</option>
                  <option value="none">ללא סיכון בלבד</option>
                </select>
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium">יתרת זכויות מינ׳ (מ״ר)</label>
                <Input {...register('remaining_rights_min')} placeholder="20" type="number" />
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium">התראות</label>
                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2">
                    <input type="checkbox" {...register('notify_email')} className="rounded" />
                    <span className="text-sm">Email</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input type="checkbox" {...register('notify_whatsapp')} className="rounded" />
                    <span className="text-sm">WhatsApp</span>
                  </label>
                </div>
              </div>
              
              <div className="md:col-span-2">
                <Button type="submit" disabled={isSubmitting} className="w-full">
                  {isSubmitting ? 'שומר...' : 'שמור חוק התראה'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
        {/* Existing alerts */}
        <Card>
          <CardHeader>
            <CardTitle>התראות קיימות</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <THead>
                <TR>
                  <TH>ID</TH>
                  <TH>עיר</TH>
                  <TH>מחיר מקס'</TH>
                  <TH>חדרים</TH>
                  <TH>סיכון</TH>
                  <TH>ערוצים</TH>
                </TR>
              </THead>
              <TBody>
                {alerts.length === 0 ? (
                  <TR>
                    <TD colSpan={6} className="text-center text-muted-foreground">לא קיימות התראות</TD>
                  </TR>
                ) : (
                  alerts.map(a => (
                    <TR key={a.id}>
                      <TD>{a.id}</TD>
                      <TD>{a.criteria?.city || '—'}</TD>
                      <TD>{a.criteria?.max_price ?? '—'}</TD>
                      <TD>{a.criteria?.beds ? `${a.criteria.beds.min ?? ''}-${a.criteria.beds.max ?? ''}` : '—'}</TD>
                      <TD>{a.criteria?.risk === 'none' ? 'ללא' : 'כל'}</TD>
                      <TD>{(a.notify || []).join(', ') || '—'}</TD>
                    </TR>
                  ))
                )}
              </TBody>
            </Table>
          </CardContent>
        </Card>

        {/* Info */}
        <Card>
          <CardHeader>
            <CardTitle>איך זה עובד?</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-3">
              <div className="text-center">
                <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center mx-auto mb-2">
                  <span className="text-primary-foreground font-bold">1</span>
                </div>
                <h3 className="font-medium">הגדרת תנאים</h3>
                <p className="text-sm text-muted-foreground">הגדירו את הקריטריונים שלכם לנכס המושלם</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center mx-auto mb-2">
                  <span className="text-primary-foreground font-bold">2</span>
                </div>
                <h3 className="font-medium">ניטור אוטומטי</h3>
                <p className="text-sm text-muted-foreground">המערכת תבדוק נכסים חדשים כל יום</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center mx-auto mb-2">
                  <span className="text-primary-foreground font-bold">3</span>
                </div>
                <h3 className="font-medium">התראה מיידית</h3>
                <p className="text-sm text-muted-foreground">קבלו הודעה ברגע שנמצא נכס מתאים</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="text-xs text-muted-foreground">
          שרת: {process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/api/alerts/
        </div>
      </div>
    </DashboardLayout>
  )
}