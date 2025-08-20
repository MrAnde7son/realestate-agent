'use client'

import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Mail, Lock, User, Building, Eye, EyeOff } from 'lucide-react'
import Logo from '@/components/Logo'
import { useAuth } from '@/lib/auth-context'
import { LoginCredentials, RegisterCredentials } from '@/lib/auth'

const loginSchema = z.object({
  email: z.string().email('דוא״ל לא תקין'),
  password: z.string().min(6, 'סיסמה חייבת להכיל לפחות 6 תווים'),
})

const registerSchema = z.object({
  email: z.string().email('דוא״ל לא תקין'),
  password: z.string().min(6, 'סיסמה חייבת להכיל לפחות 6 תווים'),
  confirmPassword: z.string(),
  username: z.string().min(3, 'שם משתמש חייב להכיל לפחות 3 תווים'),
  first_name: z.string().min(2, 'שם פרטי חייב להכיל לפחות 2 תווים'),
  last_name: z.string().min(2, 'שם משפחה חייב להכיל לפחות 2 תווים'),
  company: z.string().optional(),
  role: z.string().optional(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "סיסמאות אינן תואמות",
  path: ["confirmPassword"],
})

type LoginFormData = z.infer<typeof loginSchema>
type RegisterFormData = z.infer<typeof registerSchema>

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [error, setError] = useState('')
  const { login, register, googleLogin, isLoading } = useAuth()

  const loginForm = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  })

  const registerForm = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  })

  const onLoginSubmit = async (data: LoginFormData) => {
    try {
      setError('')
      await login(data)
    } catch (err: any) {
      setError(err.message || 'שגיאה בהתחברות')
    }
  }

  const onRegisterSubmit = async (data: RegisterFormData) => {
    try {
      setError('')
      const { confirmPassword, ...registerData } = data
      await register(registerData)
    } catch (err: any) {
      setError(err.message || 'שגיאה בהרשמה')
    }
  }

  const toggleMode = () => {
    setIsLogin(!isLogin)
    setError('')
    loginForm.reset()
    registerForm.reset()
  }

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
          <Button 
            variant={isLogin ? "default" : "ghost"} 
            className="flex-1"
            onClick={() => setIsLogin(true)}
          >
            התחברות
          </Button>
          <Button 
            variant={!isLogin ? "default" : "ghost"} 
            className="flex-1"
            onClick={() => setIsLogin(false)}
          >
            הרשמה
          </Button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-destructive/10 text-destructive text-sm p-3 rounded-lg text-center">
            {error}
          </div>
        )}

        {/* Login Form */}
        {isLogin && (
          <Card>
            <CardHeader className="text-center">
              <CardTitle>ברוכים הבאים</CardTitle>
              <CardDescription>
                התחבר לחשבון שלך כדי להמשיך
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <form onSubmit={loginForm.handleSubmit(onLoginSubmit)} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email">דוא״ל</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="email"
                      type="email"
                      placeholder="הכנס את הדוא״ל שלך"
                      className="pl-10"
                      {...loginForm.register('email')}
                    />
                  </div>
                  {loginForm.formState.errors.email && (
                    <p className="text-sm text-destructive">
                      {loginForm.formState.errors.email.message}
                    </p>
                  )}
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="password">סיסמה</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      placeholder="הכנס את הסיסמה שלך"
                      className="pl-10 pr-10"
                      {...loginForm.register('password')}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      {showPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                  {loginForm.formState.errors.password && (
                    <p className="text-sm text-destructive">
                      {loginForm.formState.errors.password.message}
                    </p>
                  )}
                </div>

                <Button 
                  type="submit" 
                  className="w-full" 
                  size="lg"
                  disabled={isLoading}
                >
                  {isLoading ? 'מתחבר...' : 'התחבר'}
                </Button>
              </form>

              <Separator />

              <Button 
                variant="outline" 
                className="w-full" 
                size="lg" 
                onClick={() => googleLogin()}
                disabled={isLoading}
              >
                <Building className="h-4 w-4 ml-2" />
                התחבר עם Google
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Register Form */}
        {!isLogin && (
          <Card>
            <CardHeader className="text-center">
              <CardTitle>הרשמה</CardTitle>
              <CardDescription>
                צור חשבון חדש כדי להתחיל
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <form onSubmit={registerForm.handleSubmit(onRegisterSubmit)} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="first_name">שם פרטי</Label>
                    <Input
                      id="first_name"
                      placeholder="שם פרטי"
                      {...registerForm.register('first_name')}
                    />
                    {registerForm.formState.errors.first_name && (
                      <p className="text-sm text-destructive">
                        {registerForm.formState.errors.first_name.message}
                      </p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="last_name">שם משפחה</Label>
                    <Input
                      id="last_name"
                      placeholder="שם משפחה"
                      {...registerForm.register('last_name')}
                    />
                    {registerForm.formState.errors.last_name && (
                      <p className="text-sm text-destructive">
                        {registerForm.formState.errors.last_name.message}
                      </p>
                    )}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="username">שם משתמש</Label>
                  <Input
                    id="username"
                    placeholder="שם משתמש"
                    {...registerForm.register('username')}
                  />
                  {registerForm.formState.errors.username && (
                    <p className="text-sm text-destructive">
                      {registerForm.formState.errors.username.message}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">דוא״ל</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="הכנס את הדוא״ל שלך"
                    {...registerForm.register('email')}
                  />
                  {registerForm.formState.errors.email && (
                    <p className="text-sm text-destructive">
                      {registerForm.formState.errors.email.message}
                    </p>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="company">חברה</Label>
                    <Input
                      id="company"
                      placeholder="שם החברה (אופציונלי)"
                      {...registerForm.register('company')}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="role">תפקיד</Label>
                    <Input
                      id="role"
                      placeholder="תפקיד (אופציונלי)"
                      {...registerForm.register('role')}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password">סיסמה</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      placeholder="הכנס סיסמה"
                      className="pl-10 pr-10"
                      {...registerForm.register('password')}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      {showPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                  {registerForm.formState.errors.password && (
                    <p className="text-sm text-destructive">
                      {registerForm.formState.errors.password.message}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirmPassword">אימות סיסמה</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="confirmPassword"
                      type={showConfirmPassword ? "text" : "password"}
                      placeholder="אמת את הסיסמה שלך"
                      className="pl-10 pr-10"
                      {...registerForm.register('confirmPassword')}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    >
                      {showConfirmPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                  {registerForm.formState.errors.confirmPassword && (
                    <p className="text-sm text-destructive">
                      {registerForm.formState.errors.confirmPassword.message}
                    </p>
                  )}
                </div>

                <Button 
                  type="submit" 
                  className="w-full" 
                  size="lg"
                  disabled={isLoading}
                >
                  {isLoading ? 'נרשם...' : 'הירשם'}
                </Button>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Footer */}
        <div className="text-center text-sm text-muted-foreground">
          <p>
            {isLogin ? 'אין לך חשבון? ' : 'יש לך כבר חשבון? '}
            <Button variant="link" className="p-0 text-sm" onClick={toggleMode}>
              {isLogin ? 'הירשם עכשיו' : 'התחבר עכשיו'}
            </Button>
          </p>
        </div>
      </div>
    </div>
  )
}
