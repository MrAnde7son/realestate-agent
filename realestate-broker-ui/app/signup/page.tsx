'use client'

import { useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'

export default function SignupPage() {
  const router = useRouter()
  const searchParams = useSearchParams()

  useEffect(() => {
    // Get any existing redirect parameter from the current URL
    const redirectTo = searchParams.get('redirect')
    
    // Build the auth URL with signup mode and preserve redirect parameter
    const authUrl = redirectTo 
      ? `/auth?mode=signup&redirect=${encodeURIComponent(redirectTo)}`
      : '/auth?mode=signup'
    
    // Redirect to auth page with signup mode
    router.replace(authUrl)
  }, [router, searchParams])

  // Show a loading state while redirecting
  return (
    <div className="min-h-[100dvh] flex items-center justify-center bg-background">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
        <p className="text-muted-foreground">מעביר לעמוד הרשמה...</p>
      </div>
    </div>
  )
}
