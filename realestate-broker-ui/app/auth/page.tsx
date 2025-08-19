"use client"

import React, { useState, FormEvent } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Mail, Lock, User } from 'lucide-react'
import Logo from '@/components/Logo'
import { login, register, googleLogin } from '@/lib/api'
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google'

export default function AuthPage() {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    try {
      if (mode === 'login') {
        await login(username, password)
      } else {
        await register(username, password, email)
      }
      setError(null)
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <GoogleOAuthProvider clientId={process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || ''}>
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
            <Button
              variant={mode === 'login' ? 'default' : 'ghost'}
              className="flex-1"
              onClick={() => setMode('login')}
            >
              התחברות
            </Button>
            <Button
              variant={mode === 'register' ? 'default' : 'ghost'}
              className="flex-1"
              onClick={() => setMode('register')}
            >
              הרשמה
            </Button>
          </div>

          <Card>
            <CardHeader className="text-center">
              <CardTitle>ברוכים הבאים</CardTitle>
              <CardDescription>
                {mode === 'login'
                  ? 'התחבר לחשבון שלך כדי להמשיך'
                  : 'צור חשבון חדש'}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {error && <p className="text-sm text-red-500">{error}</p>}
              <div className="space-y-2">
                <Label htmlFor="username">שם משתמש</Label>
                <div className="relative">
                  <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="שם המשתמש שלך"
                    className="pl-10"
                  />
                </div>
              </div>

              {mode === 'register' && (
                <div className="space-y-2">
                  <Label htmlFor="email">דוא״ל</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="הכנס את הדוא״ל שלך"
                      className="pl-10"
                    />
                  </div>
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="password">סיסמה</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="הכנס את הסיסמה שלך"
                    className="pl-10"
                  />
                </div>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <Button className="w-full" size="lg" type="submit">
                  {mode === 'login' ? 'התחבר' : 'הרשם'}
                </Button>
              </form>

              <Separator />

              <GoogleLogin
                onSuccess={(cred) => {
                  if (cred.credential) {
                    googleLogin(cred.credential)
                  }
                }}
                onError={() => setError('Google login failed')}
              />
            </CardContent>
          </Card>

          {/* Footer */}
          <div className="text-center text-sm text-muted-foreground">
            {mode === 'login' ? (
              <p>
                אין לך חשבון?{' '}
                <Button variant="link" className="p-0 text-sm" onClick={() => setMode('register')}>
                  הירשם עכשיו
                </Button>
              </p>
            ) : (
              <p>
                כבר רשום?{' '}
                <Button variant="link" className="p-0 text-sm" onClick={() => setMode('login')}>
                  התחבר
                </Button>
              </p>
            )}
          </div>
        </div>
      </div>
    </GoogleOAuthProvider>
  )
}
