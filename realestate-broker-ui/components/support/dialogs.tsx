import { useState, FormEvent } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export function ContactSupportDialog({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false)
  const [pending, setPending] = useState(false)

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = new FormData(e.currentTarget)
    const body = {
      subject: form.get('subject'),
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
        alert('!הבקשה נשלחה בהצלחה')
        setOpen(false)
      } else {
        alert('אירעה שגיאה, נסה שוב')
      }
    } catch (e) {
      alert('אירעה שגיאה, נסה שוב')
    } finally {
      setPending(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>צור קשר עם התמיכה</DialogTitle>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-4">
          <Input name="subject" placeholder="נושא" required />
          <textarea name="message" className="w-full border rounded p-2" placeholder="הודעה" required />
          <DialogFooter>
            <Button type="submit" disabled={pending}>שלח</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export function BugReportDialog({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false)
  const [pending, setPending] = useState(false)

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = new FormData(e.currentTarget)
    form.append('url', window.location.href)
    form.append('user_agent', navigator.userAgent)
    form.append('app_version', process.env.NEXT_PUBLIC_APP_VERSION || '')
    setPending(true)
    try {
      const res = await fetch('/api/support/bug', {
        method: 'POST',
        body: form,
      })
      if (res.ok) {
        alert('!הבקשה נשלחה בהצלחה')
        setOpen(false)
      } else {
        alert('אירעה שגיאה, נסה שוב')
      }
    } catch (e) {
      alert('אירעה שגיאה, נסה שוב')
    } finally {
      setPending(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>דווח על באג</DialogTitle>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-4">
          <Input name="subject" placeholder="נושא" />
          <textarea name="message" className="w-full border rounded p-2" placeholder="תיאור" required />
          <Input name="attachment" type="file" />
          <DialogFooter>
            <Button type="submit" disabled={pending}>שלח</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export function ConsultationDialog({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false)
  const [pending, setPending] = useState(false)

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = new FormData(e.currentTarget)
    const body = {
      full_name: form.get('full_name'),
      email: form.get('email'),
      phone: form.get('phone'),
      preferred_time: form.get('preferred_time'),
      channel: form.get('channel'),
      topic: form.get('topic'),
    }
    setPending(true)
    try {
      const res = await fetch('/api/support/consultation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (res.ok) {
        alert('!הבקשה נשלחה בהצלחה')
        setOpen(false)
      } else {
        alert('אירעה שגיאה, נסה שוב')
      }
    } catch (e) {
      alert('אירעה שגיאה, נסה שוב')
    } finally {
      setPending(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>הזמן שיחת ייעוץ</DialogTitle>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-4">
          <Input name="full_name" placeholder="שם מלא" required />
          <Input name="email" type="email" placeholder="אימייל" required />
          <Input name="phone" placeholder="טלפון" required />
          <Input name="preferred_time" placeholder="זמן מועדף" required />
          <Input name="channel" placeholder="ערוץ" required />
          <Input name="topic" placeholder="נושא" />
          <DialogFooter>
            <Button type="submit" disabled={pending}>שלח</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
