import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Mail, Lock, User, Building } from 'lucide-react'
import Logo from '@/components/Logo'

export default function AuthPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-md space-y-6">
        {/* Logo */}
        <div className="text-center">
          <Logo variant="horizontal" size={48} color="var(--brand-teal)" />
          <h1 className="text-2xl font-bold text-foreground mt-4">נדל״נר</h1>
          <p className="text-muted-foreground">נדל״ן חכם לשמאים, מתווכים ומשקיעים</p>
        </div>

        {/* Auth Tabs */}
        <div className="flex space-x-1 bg-muted p-1 rounded-lg">
          <Button variant="default" className="flex-1">התחברות</Button>
          <Button variant="ghost" className="flex-1">הרשמה</Button>
        </div>

        {/* Login Form */}
        <Card>
          <CardHeader className="text-center">
            <CardTitle>ברוכים הבאים</CardTitle>
            <CardDescription>
              התחבר לחשבון שלך כדי להמשיך
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">דוא״ל</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  placeholder="הכנס את הדוא״ל שלך"
                  className="pl-10"
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="password">סיסמה</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  id="password"
                  type="password"
                  placeholder="הכנס את הסיסמה שלך"
                  className="pl-10"
                />
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="remember"
                  className="rounded border-gray-300"
                />
                <Label htmlFor="remember" className="text-sm">
                  זכור אותי
                </Label>
              </div>
              <Button variant="link" className="text-sm p-0">
                שכחת סיסמה?
              </Button>
            </div>

            <Button className="w-full" size="lg">
              התחבר
            </Button>

            <Separator />

            <Button variant="outline" className="w-full" size="lg">
              <Building className="h-4 w-4 ml-2" />
              התחבר עם Google
            </Button>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center text-sm text-muted-foreground">
          <p>אין לך חשבון? </p>
          <Button variant="link" className="p-0 text-sm">
            הירשם עכשיו
          </Button>
        </div>
      </div>
    </div>
  )
}
