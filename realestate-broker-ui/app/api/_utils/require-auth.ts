import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { validateToken } from '@/lib/token-utils'

/**
 * Check if the request is authenticated
 * Returns null if authenticated, or a redirect response if not authenticated
 */
export async function requireAuth(req: Request): Promise<NextResponse | null> {
  const cookieStore = await cookies()
  let token = cookieStore.get('access_token')?.value
  
  // Also check Authorization header for API tokens
  if (!token) {
    const authHeader = req.headers.get('authorization')
    if (authHeader && authHeader.startsWith('Bearer ')) {
      token = authHeader.substring(7)
    }
  }
  
  // If no token at all, redirect to auth
  if (!token) {
    return NextResponse.redirect(new URL('/auth', req.url))
  }
  
  // Validate token only if it's a JWT (has 3 parts separated by dots)
  // API tokens are not JWTs, so we skip validation and let the backend handle them
  const isJWT = token.split('.').length === 3
  if (isJWT) {
    const tokenValidation = validateToken(token)
    if (!tokenValidation.isValid) {
      // Clear invalid tokens and redirect to auth
      const response = NextResponse.redirect(new URL('/auth', req.url))
      response.cookies.delete('access_token')
      response.cookies.delete('refresh_token')
      return response
    }
  }
  
  // Token exists and is valid (or is an API token that backend will validate)
  return null
}

