'use client'

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuth } from '@/lib/auth-context'
import { PageLoader } from '@/components/ui/page-loader'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react'

export default function GoogleCallbackPage() {
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [error, setError] = useState<string>('')
  const router = useRouter()
  const searchParams = useSearchParams()
  const { refreshUser } = useAuth()

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Get tokens from URL parameters
        const accessToken = searchParams.get('access_token')
        const refreshToken = searchParams.get('refresh_token')

        if (!accessToken || !refreshToken) {
          setError('Missing authentication tokens from Google')
          setStatus('error')
          return
        }

        // Store tokens
        const { authAPI } = await import('@/lib/auth')
        authAPI.setTokens(accessToken, refreshToken)

        // Refresh user profile to update auth context
        await refreshUser()
        
        setStatus('success')
        
        // Redirect to home page after a short delay
        setTimeout(() => {
          router.push('/')
        }, 2000)
        
      } catch (err: any) {
        console.error('Google callback error:', err)
        setError(err.message || 'Failed to complete Google authentication')
        setStatus('error')
      }
    }

    handleCallback()
  }, [searchParams, router, refreshUser])

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center space-y-4">
          <PageLoader />
          <p className="text-muted-foreground">משלים התחברות עם Google...</p>
        </div>
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4">
              <XCircle className="h-16 w-16 text-destructive" />
            </div>
            <CardTitle className="text-xl">שגיאה בהתחברות</CardTitle>
            <CardDescription>
              לא ניתן היה להשלים את ההתחברות עם Google
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-destructive/10 text-destructive text-sm p-3 rounded-lg">
              {error}
            </div>
            <Button 
              onClick={() => router.push('/auth')} 
              className="w-full"
            >
              חזור לדף התחברות
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4">
            <CheckCircle className="h-16 w-16 text-green-500" />
          </div>
          <CardTitle className="text-xl">התחברות הושלמה בהצלחה!</CardTitle>
          <CardDescription>
            אתה מועבר לדף הבית...
          </CardDescription>
        </CardHeader>
        <CardContent className="text-center">
          <div className="flex items-center justify-center space-x-2 text-muted-foreground">
            <AlertCircle className="h-4 w-4" />
            <span>אם לא תועבר אוטומטית, לחץ על הכפתור למטה</span>
          </div>
          <Button 
            onClick={() => router.push('/')} 
            className="w-full mt-4"
          >
            עבור לדף הבית
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
