import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { validateToken } from './lib/token-utils'

// Routes that require authentication
const protectedRoutes = [
  '/alerts',
  '/reports',
  '/profile',
  '/settings',
  '/admin',
  '/crm'
]

export async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl
  
  // Check if the route requires authentication
  const isProtectedRoute = protectedRoutes.some(route => 
    pathname === route || pathname.startsWith(route)
  )
  
  // Check if the route is the auth page
  const isAuthRoute = pathname === '/auth' || pathname.startsWith('/auth')
  
  // Get the token from cookies
  const accessToken = request.cookies.get('access_token')?.value
  const refreshToken = request.cookies.get('refresh_token')?.value
  
  // Debug logging
  console.log(`🔍 Proxy: ${pathname}`, {
    isProtectedRoute,
    isAuthRoute,
    hasAccessToken: !!accessToken,
    hasRefreshToken: !!refreshToken,
    cookies: request.cookies.getAll().map(c => c.name)
  })
  
  // Check if we have a valid token (either access or refresh token)
  const hasValidToken = accessToken || refreshToken

  // Validate access token if present
  let isTokenExpired = false
  let needsRefresh = false
  
  if (accessToken) {
    const tokenValidation = validateToken(accessToken)
    isTokenExpired = tokenValidation.isExpired
    needsRefresh = tokenValidation.needsRefresh
    
    if (tokenValidation.isExpired) {
      console.log('🔄 Access token is expired in proxy')
    }
  }
  
  // If access token is expired but we have a refresh token, we can still allow access
  // The frontend will handle the token refresh
  const canAccess = hasValidToken && (!isTokenExpired || refreshToken)
  
  // If it's a protected route and no valid token or can't access, redirect to auth
  if (isProtectedRoute && !canAccess) {
    console.log(`🔒 Redirecting to auth: ${pathname} requires authentication (expired: ${isTokenExpired}, hasRefresh: ${!!refreshToken})`)
    return NextResponse.redirect(new URL('/auth', request.url))
  }
  
  // If it's the auth page and user has valid non-expired access token, redirect appropriately
  // Allow access to auth page if only refresh token is available (for token refresh)
  if (isAuthRoute && accessToken && !isTokenExpired) {
    // Check if there's a redirect parameter in the URL
    const redirectParam = request.nextUrl.searchParams.get('redirect')
    
    if (redirectParam) {
      // Check if redirect is to an OAuth endpoint - if so, allow access to auth page
      // so the frontend can establish Django session before redirecting
      const isOAuthRedirect = redirectParam.includes('/oauth/authorize') || 
                              redirectParam.includes('/mcp/oauth')
      
      if (isOAuthRedirect) {
        // Don't redirect - let the auth page handle OAuth flow (it will establish session)
        console.log(`🔄 Allowing access to auth page for OAuth redirect: ${redirectParam}`)
        return NextResponse.next()
      } else {
        // Non-OAuth redirect - redirect directly
        console.log(`🔄 Redirecting to specified redirect URL: ${redirectParam}`)
        // If it's an absolute URL, redirect directly; otherwise construct full URL
        if (redirectParam.startsWith('http://') || redirectParam.startsWith('https://')) {
          return NextResponse.redirect(redirectParam)
        } else {
          // Relative URL - construct full URL
          const redirectUrl = new URL(redirectParam, request.url)
          return NextResponse.redirect(redirectUrl)
        }
      }
    } else {
      // No redirect parameter, redirect to home
      console.log(`🔄 Redirecting to home: user already authenticated with valid access token`)
      return NextResponse.redirect(new URL('/', request.url))
    }
  }

  if (pathname.startsWith('/admin')) {
    // Get the access token from cookies
    const accessToken = request.cookies.get('access_token')?.value
    
    if (!accessToken || isTokenExpired) {
      console.log(`🔒 No valid access token for admin route: ${pathname} (expired: ${isTokenExpired})`)
      return NextResponse.redirect(new URL('/', request.url))
    }
    
    try {
      const res = await fetch(`${process.env.BACKEND_URL || 'http://127.0.0.1:8000'}/api/me`, {
        headers: { 
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
      })
      
      if (res.status !== 200) {
        console.log(`🔒 API returned status ${res.status} for admin route: ${pathname}`)
        return NextResponse.redirect(new URL('/', request.url))
      }
      
      const me = await res.json()
      console.log(`👤 User role check: ${me.role} for route: ${pathname}`)
      
      if (me.role !== 'admin') {
        console.log(`🔒 User role '${me.role}' is not admin for route: ${pathname}`)
        return NextResponse.redirect(new URL('/', request.url))
      }
    } catch (error) {
      console.error(`❌ Error checking admin access for ${pathname}:`, error)
      return NextResponse.redirect(new URL('/', request.url))
    }
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!api|_next/static|_next/image|favicon.ico|public).*)'
  ]
}

