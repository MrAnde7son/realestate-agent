'use client'

import React, { useState, useEffect, useRef } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Mail, Lock, Building, Eye, EyeOff } from 'lucide-react'
import Logo from '@/components/Logo'
import { useAuth } from '@/lib/auth-context'
import { LoginCredentials, RegisterCredentials } from '@/lib/auth'
import { useSearchParams, useRouter, usePathname } from 'next/navigation'

const loginSchema = z.object({
  email: z.string().email('דוא״ל לא תקין'),
  password: z.string().min(6, 'סיסמה חייבת להכיל לפחות 6 תווים'),
})

const registerSchema = z.object({
  email: z.string().email('דוא״ל לא תקין'),
  password: z.string().min(6, 'סיסמה חייבת להכיל לפחות 6 תווים'),
  confirmPassword: z.string(),
  first_name: z.string().min(2, 'שם פרטי חייב להכיל לפחות 2 תווים'),
  last_name: z.string().min(2, 'שם משפחה חייב להכיל לפחות 2 תווים'),
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
  const { login, register, googleLogin, isLoading, isAuthenticated } = useAuth()
  const searchParams = useSearchParams()
  const router = useRouter()
  const pathname = usePathname()
  const hasRedirectedRef = useRef(false)
  
  // Get the redirect URL and mode from query parameters
  const redirectTo = searchParams.get('redirect') || '/'
  const mode = searchParams.get('mode')
  
  // Set initial mode based on URL parameter
  useEffect(() => {
    if (mode === 'signup') {
      setIsLogin(false)
    } else {
      setIsLogin(true)
    }
  }, [mode])
  
  // If user is already authenticated and there's an OAuth redirect, establish session and redirect
  useEffect(() => {
    const handleOAuthRedirect = async () => {
      // Check sessionStorage to prevent loops across page reloads
      const redirectKey = `oauth_redirect_${redirectTo}`
      if (sessionStorage.getItem(redirectKey)) {
        console.log('Redirect already attempted in this session, skipping')
        return
      }
      
      // Prevent multiple redirects in the same render cycle
      if (hasRedirectedRef.current) {
        console.log('Already redirected, skipping')
        return
      }
      
      // Only proceed if user is authenticated, has redirect, and it's an OAuth endpoint
      if (!isAuthenticated || !redirectTo || (!redirectTo.includes('/oauth/authorize') && !redirectTo.includes('/mcp/oauth'))) {
        return
      }
      
      // Mark as redirecting immediately to prevent loops
      hasRedirectedRef.current = true
      sessionStorage.setItem(redirectKey, 'true')
      console.log('Starting OAuth redirect flow to:', redirectTo)
      
      try {
        const { authAPI } = await import('@/lib/auth')
        // Establish Django session for OAuth flow
        console.log('Establishing Django session...')
        await authAPI.establishSession()
        console.log('Session established, redirecting to:', redirectTo)
        
        // Clear the flag after a delay to allow redirect to complete
        // Redirect immediately without setTimeout to prevent React from interfering
        window.location.replace(redirectTo)
      } catch (error) {
        console.error('Failed to establish session for OAuth redirect:', error)
        // If session establishment fails, show error but don't redirect
        setError('שגיאה בהתחברות לשרת. נסה שוב.')
        hasRedirectedRef.current = false
        sessionStorage.removeItem(redirectKey)
      }
    }
    
    // Only run if we have the necessary conditions
    if (isAuthenticated !== undefined) {
      handleOAuthRedirect()
    }
  }, [isAuthenticated, redirectTo])

  const loginForm = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  })

  const registerForm = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  })

  const onLoginSubmit = async (data: LoginFormData) => {
    try {
      setError('')
      console.log('Login form submitted, redirectTo:', redirectTo)
      // The login function will handle the redirect
      await login(data, redirectTo)
    } catch (err: any) {
      setError(err.message || 'שגיאה בהתחברות')
    }
  }

  const onRegisterSubmit = async (data: RegisterFormData) => {
    try {
      setError('')
      const { confirmPassword, ...registerData } = data
      const payload: RegisterCredentials = { ...registerData }
      await register(payload, redirectTo)
    } catch (err: any) {
      setError(err.message || 'שגיאה בהרשמה')
    }
  }

  const handleModeChange = React.useCallback((nextMode: 'login' | 'signup') => {
    if ((nextMode === 'login' && isLogin) || (nextMode === 'signup' && !isLogin)) {
      return
    }

    setIsLogin(nextMode === 'login')
    setError('')
    loginForm.reset()
    registerForm.reset()

    const params = new URLSearchParams(searchParams.toString())

    if (nextMode === 'signup') {
      params.set('mode', 'signup')
    } else {
      params.delete('mode')
    }

    const paramsString = params.toString()

    router.replace(paramsString ? `${pathname}?${paramsString}` : pathname, { scroll: false })
  }, [isLogin, loginForm, registerForm, pathname, router, searchParams])

  return (
    <div className="min-h-[100dvh] flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-md space-y-6">
        {/* Logo */}
        <div className="text-center">
          <Logo variant="horizontal" size={48} color="hsl(var(--primary))" />
          <h1 className="text-2xl font-bold text-foreground mt-4">נדל״נר</h1>
          <p className="text-muted-foreground">נדל״ן חכם לאנשים פרטיים ומתווכים</p>
        </div>

        {/* Auth Tabs */}
        <div className="flex space-x-1 rtl:space-x-reverse bg-muted p-1 rounded-lg">
          <Button 
            variant={isLogin ? "default" : "ghost"} 
            className="flex-1"
            onClick={() => handleModeChange('login')}
          >
            התחברות
          </Button>
          <Button 
            variant={!isLogin ? "default" : "ghost"} 
            className="flex-1"
            onClick={() => handleModeChange('signup')}
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
                    <Mail className="absolute start-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="email"
                      type="email"
                      placeholder="הכנס את הדוא״ל שלך"
                      className="ps-10 pe-10"
                      dir="rtl"
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
                    <Lock className="absolute start-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      placeholder="הכנס את הסיסמה שלך"
                      className="ps-10 pe-10"
                      dir="rtl"
                      {...loginForm.register('password')}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute end-0 top-0 h-full px-3 py-2 hover:bg-transparent"
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

                <div className="space-y-2">
                  <div className="flex items-center justify-center">
                    <span className="text-xs text-teal-600 dark:text-teal-400 font-medium">🎉 תקופת הרצה – שימוש חופשי ללא עלות</span>
                  </div>
                  <Button 
                    type="submit" 
                    className="w-full" 
                    size="lg"
                    disabled={isLoading}
                  >
                    {isLoading ? 'מתחבר...' : 'התחבר'}
                  </Button>
                </div>
              </form>

              <Separator />

              <div className="space-y-2">
                <Button 
                  variant="outline" 
                  className="w-full" 
                  size="lg" 
                  onClick={() => googleLogin(redirectTo)}
                  disabled={isLoading}
                >
                  <Building className="h-4 w-4 ms-2" />
                  התחבר עם Google
                </Button>
              </div>
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
                      dir="rtl"
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
                      dir="rtl"
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
                  <Label htmlFor="email">דוא״ל</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="הכנס את הדוא״ל שלך"
                    dir="rtl"
                    {...registerForm.register('email')}
                  />
                  {registerForm.formState.errors.email && (
                    <p className="text-sm text-destructive">
                      {registerForm.formState.errors.email.message}
                    </p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password">סיסמה</Label>
                  <div className="relative">
                    <Lock className="absolute start-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      placeholder="הכנס סיסמה"
                      className="ps-10 pe-10"
                      dir="rtl"
                      {...registerForm.register('password')}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute end-0 top-0 h-full px-3 py-2 hover:bg-transparent"
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
                    <Lock className="absolute start-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="confirmPassword"
                      type={showConfirmPassword ? "text" : "password"}
                      placeholder="אמת את הסיסמה שלך"
                      className="ps-10 pe-10"
                      dir="rtl"
                      {...registerForm.register('confirmPassword')}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute end-0 top-0 h-full px-3 py-2 hover:bg-transparent"
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

                <div className="space-y-2">
                  <div className="flex items-center justify-center">
                    <span className="text-xs text-teal-600 dark:text-teal-400 font-medium">🎉 תקופת הרצה – שימוש חופשי ללא עלות</span>
                  </div>
                  <Button
                    type="submit"
                    className="w-full"
                    size="lg"
                    disabled={isLoading}
                  >
                    {isLoading ? 'נרשם...' : 'הירשם'}
                  </Button>
                </div>
              </form>

              <Separator />

              <div className="space-y-2">
                <Button
                  variant="outline"
                  className="w-full"
                  size="lg"
                  onClick={() => googleLogin(redirectTo)}
                  disabled={isLoading}
                >
                  <Building className="h-4 w-4 ms-2" />
                  הירשם עם Google
                </Button>
                <p className="text-xs text-center text-muted-foreground">
                  התחברות עם Google כדי להתחיל במהירות, ללא צורך בהגדרות נוספות.
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Footer */}
        <div className="text-center text-sm text-muted-foreground">
          <p>
            {isLogin ? 'אין לך חשבון? ' : 'יש לך כבר חשבון? '}
            <Button
              variant="link"
              className="p-0 text-sm"
              onClick={() => handleModeChange(isLogin ? 'signup' : 'login')}
            >
              {isLogin ? 'הירשם עכשיו' : 'התחבר עכשיו'}
            </Button>
          </p>
        </div>
      </div>
    </div>
  )
}
