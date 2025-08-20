'use client'

import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import DashboardLayout from '@/components/layout/dashboard-layout'
import { DashboardShell, DashboardHeader } from '@/components/layout/dashboard-shell'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { User, Mail, Phone, MapPin, Building, Shield, Key, Star, Save, Edit } from 'lucide-react'
import { useAuth } from '@/lib/auth-context'
import { ProfileUpdateData } from '@/lib/auth'

const profileSchema = z.object({
  first_name: z.string().min(2, 'שם פרטי חייב להכיל לפחות 2 תווים'),
  last_name: z.string().min(2, 'שם משפחה חייב להכיל לפחות 2 תווים'),
  company: z.string().optional(),
  role: z.string().optional(),
})

type ProfileFormData = z.infer<typeof profileSchema>

export default function ProfilePage() {
  const { user, updateProfile } = useAuth()
  const [isEditing, setIsEditing] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const form = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
      company: user?.company || '',
      role: user?.role || '',
    },
  })

  // Update form values when user changes
  React.useEffect(() => {
    if (user) {
      form.reset({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        company: user.company || '',
        role: user.role || '',
      })
    }
  }, [user, form])

  const onSubmit = async (data: ProfileFormData) => {
    try {
      setIsLoading(true)
      setError('')
      setSuccess('')
      
      await updateProfile(data)
      setSuccess('הפרופיל עודכן בהצלחה!')
      setIsEditing(false)
    } catch (err: any) {
      setError(err.message || 'שגיאה בעדכון הפרופיל')
    } finally {
      setIsLoading(false)
    }
  }

  const handleEdit = () => {
    setIsEditing(true)
    setError('')
    setSuccess('')
  }

  const handleCancel = () => {
    setIsEditing(false)
    form.reset()
    setError('')
    setSuccess('')
  }

  const getUserInitials = () => {
    if (user?.first_name && user?.last_name) {
      return `${user.first_name[0]}${user.last_name[0]}`
    }
    if (user?.username) {
      return user.username.substring(0, 2).toUpperCase()
    }
    if (user?.email) {
      return user.email.substring(0, 2).toUpperCase()
    }
    return 'משתמש'
  }

  if (!user) {
    return null
  }

  return (
    <DashboardLayout>
      <DashboardShell>
        <DashboardHeader 
          heading="פרופיל אישי" 
          text="נהל את המידע האישי והגדרות החשבון שלך" 
        />
        
        <div className="grid gap-6 grid-cols-1 lg:grid-cols-3">
          {/* Profile Overview */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader className="text-center">
                <div className="flex justify-center mb-4">
                  <Avatar className="h-24 w-24">
                    <AvatarFallback className="text-2xl">{getUserInitials()}</AvatarFallback>
                  </Avatar>
                </div>
                <CardTitle className="text-xl">
                  {user.first_name && user.last_name 
                    ? `${user.first_name} ${user.last_name}`
                    : user.username || user.email
                  }
                </CardTitle>
                <CardDescription>
                  {user.role || 'משתמש'}
                  {user.company && ` • ${user.company}`}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-3 text-sm">
                  <Mail className="h-4 w-4 text-muted-foreground" />
                  <span>{user.email}</span>
                </div>
                {user.company && (
                  <div className="flex items-center gap-3 text-sm">
                    <Building className="h-4 w-4 text-muted-foreground" />
                    <span>{user.company}</span>
                  </div>
                )}
                <div className="flex items-center gap-3 text-sm">
                  <Shield className="h-4 w-4 text-muted-foreground" />
                  <span className={user.is_verified ? 'text-green-600' : 'text-orange-600'}>
                    {user.is_verified ? 'מאומת' : 'לא מאומת'}
                  </span>
                </div>
                {user.created_at && (
                  <div className="flex items-center gap-3 text-sm">
                    <Star className="h-4 w-4 text-muted-foreground" />
                    <span>חבר מאז {new Date(user.created_at).toLocaleDateString('he-IL')}</span>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Profile Form */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>פרטים אישיים</CardTitle>
                    <CardDescription>
                      עדכן את המידע האישי שלך
                    </CardDescription>
                  </div>
                  {!isEditing && (
                    <Button onClick={handleEdit} variant="outline" size="sm">
                      <Edit className="h-4 w-4 ml-2" />
                      ערוך
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {error && (
                  <div className="bg-destructive/10 text-destructive text-sm p-3 rounded-lg mb-4">
                    {error}
                  </div>
                )}
                
                {success && (
                  <div className="bg-green-100 text-green-800 text-sm p-3 rounded-lg mb-4">
                    {success}
                  </div>
                )}

                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="first_name">שם פרטי</Label>
                      <Input
                        id="first_name"
                        {...form.register('first_name')}
                        disabled={!isEditing}
                      />
                      {form.formState.errors.first_name && (
                        <p className="text-sm text-destructive">
                          {form.formState.errors.first_name.message}
                        </p>
                      )}
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="last_name">שם משפחה</Label>
                      <Input
                        id="last_name"
                        {...form.register('last_name')}
                        disabled={!isEditing}
                      />
                      {form.formState.errors.last_name && (
                        <p className="text-sm text-destructive">
                          {form.formState.errors.last_name.message}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="company">חברה</Label>
                      <Input
                        id="company"
                        {...form.register('company')}
                        disabled={!isEditing}
                        placeholder="שם החברה (אופציונלי)"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="role">תפקיד</Label>
                      <Input
                        id="role"
                        {...form.register('role')}
                        disabled={!isEditing}
                        placeholder="תפקיד (אופציונלי)"
                      />
                    </div>
                  </div>

                  {isEditing && (
                    <div className="flex gap-3 pt-4">
                      <Button type="submit" disabled={isLoading}>
                        {isLoading ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                            שומר...
                          </>
                        ) : (
                          <>
                            <Save className="h-4 w-4 ml-2" />
                            שמור שינויים
                          </>
                        )}
                      </Button>
                      <Button type="button" variant="outline" onClick={handleCancel}>
                        ביטול
                      </Button>
                    </div>
                  )}
                </form>
              </CardContent>
            </Card>

            {/* Account Security */}
            <Card className="mt-6">
              <CardHeader>
                <CardTitle>אבטחה וחשבון</CardTitle>
                <CardDescription>
                  הגדרות אבטחה וניהול חשבון
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <Key className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <div className="font-medium">סיסמה</div>
                      <div className="text-sm text-muted-foreground">
                        עדכן את הסיסמה שלך
                      </div>
                    </div>
                  </div>
                  <Button variant="outline" size="sm" disabled>
                    שנה סיסמה
                  </Button>
                </div>

                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <Shield className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <div className="font-medium">אימות דו-שלבי</div>
                      <div className="text-sm text-muted-foreground">
                        הוסף שכבת אבטחה נוספת
                      </div>
                    </div>
                  </div>
                  <Button variant="outline" size="sm" disabled>
                    הפעל
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </DashboardShell>
    </DashboardLayout>
  )
}
