"use client"

import React, { useState, FormEvent } from 'react'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { DashboardShell, DashboardHeader } from '@/components/layout/dashboard-shell'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Mail, Phone, MapPin, Clock, MessageSquare, HelpCircle } from 'lucide-react'

export default function ContactPage() {
  const [pending, setPending] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = new FormData(e.currentTarget)
    const body = {
      name: form.get('name'),
      email: form.get('email'),
      phone: form.get('phone'),
      subject: form.get('subject'),
      category: form.get('category'),
      message: form.get('message'),
    }
    setPending(true)
    try {
      const res = await fetch('/api/support/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (res.ok) {
        setSubmitted(true)
      } else {
        alert('אירעה שגיאה, נסה שוב')
      }
    } catch (e) {
      alert('אירעה שגיאה, נסה שוב')
    } finally {
      setPending(false)
    }
  }

  if (submitted) {
    return (
      <DashboardLayout>
        <DashboardShell>
          <DashboardHeader heading="הודעה נשלחה בהצלחה" />
          <Card>
            <CardContent className="text-center py-8">
              <div className="text-green-600 text-6xl mb-4">✓</div>
              <h2 className="text-2xl font-bold mb-4">תודה על פנייתך!</h2>
              <p className="text-neutral-600 mb-6">
                קיבלנו את הודעתך ונחזור אליך תוך 24 שעות.
              </p>
              <Button onClick={() => setSubmitted(false)}>
                שלח הודעה נוספת
              </Button>
            </CardContent>
          </Card>
        </DashboardShell>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <DashboardShell>
        <DashboardHeader heading="צור קשר" />
        <div className="grid md:grid-cols-2 gap-8">
          {/* Contact Form */}
          <Card>
            <CardHeader>
              <CardTitle>שלח לנו הודעה</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={onSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="name">שם מלא *</Label>
                    <Input name="name" id="name" required />
                  </div>
                  <div>
                    <Label htmlFor="email">אימייל *</Label>
                    <Input name="email" type="email" id="email" required />
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="phone">טלפון</Label>
                    <Input name="phone" id="phone" />
                  </div>
                  <div>
                    <Label htmlFor="category">קטגוריה *</Label>
                    <Select name="category" required>
                      <SelectTrigger>
                        <SelectValue placeholder="בחר קטגוריה" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="support">תמיכה טכנית</SelectItem>
                        <SelectItem value="billing">חיוב ותשלומים</SelectItem>
                        <SelectItem value="feature">בקשה לתכונה חדשה</SelectItem>
                        <SelectItem value="bug">דיווח על באג</SelectItem>
                        <SelectItem value="partnership">שותפות עסקית</SelectItem>
                        <SelectItem value="other">אחר</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div>
                  <Label htmlFor="subject">נושא *</Label>
                  <Input name="subject" id="subject" required />
                </div>

                <div>
                  <Label htmlFor="message">הודעה *</Label>
                  <textarea 
                    name="message" 
                    id="message" 
                    rows={6}
                    className="w-full border rounded p-2"
                    placeholder="תאר את השאלה או הבעיה שלך בפירוט..."
                    required 
                  />
                </div>

                <Button type="submit" disabled={pending} className="w-full">
                  {pending ? 'שולח...' : 'שלח הודעה'}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Contact Information */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>פרטי יצירת קשר</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-3">
                  <Mail className="h-5 w-5 text-brand-teal" />
                  <div>
                    <p className="font-medium">אימייל</p>
                    <p className="text-sm text-neutral-600">support@nadlaner.com</p>
                  </div>
                </div>
                
                <div className="flex items-center gap-3">
                  <Phone className="h-5 w-5 text-brand-teal" />
                  <div>
                    <p className="font-medium">טלפון</p>
                    <p className="text-sm text-neutral-600">03-123-4567</p>
                  </div>
                </div>
                
                <div className="flex items-center gap-3">
                  <MapPin className="h-5 w-5 text-brand-teal" />
                  <div>
                    <p className="font-medium">כתובת</p>
                    <p className="text-sm text-neutral-600">תל אביב, ישראל</p>
                  </div>
                </div>
                
                <div className="flex items-center gap-3">
                  <Clock className="h-5 w-5 text-brand-teal" />
                  <div>
                    <p className="font-medium">שעות פעילות</p>
                    <p className="text-sm text-neutral-600">א׳-ה׳ 9:00-18:00</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>עזרה מהירה</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center gap-3 p-3 rounded-lg bg-neutral-50">
                  <HelpCircle className="h-5 w-5 text-brand-teal" />
                  <div>
                    <p className="font-medium text-sm">שאלות נפוצות</p>
                    <p className="text-xs text-neutral-600">מצא תשובות לשאלות נפוצות</p>
                  </div>
                </div>
                
                <div className="flex items-center gap-3 p-3 rounded-lg bg-neutral-50">
                  <MessageSquare className="h-5 w-5 text-brand-teal" />
                  <div>
                    <p className="font-medium text-sm">צ&apos;אט חי</p>
                    <p className="text-xs text-neutral-600">קבל עזרה מיידית מצוות התמיכה</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>זמני תגובה</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>תמיכה טכנית:</span>
                    <span className="font-medium">תוך 4 שעות</span>
                  </div>
                  <div className="flex justify-between">
                    <span>שאלות כלליות:</span>
                    <span className="font-medium">תוך 24 שעות</span>
                  </div>
                  <div className="flex justify-between">
                    <span>בקשות תכונות:</span>
                    <span className="font-medium">תוך 48 שעות</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </DashboardShell>
    </DashboardLayout>
  )
}
