import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Routes that require authentication
const protectedRoutes = [
  '/mortgage',
  '/alerts',
  '/reports',
  '/profile',
  '/settings',
  '/admin'
]

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  
  // Check if the route requires authentication
  const isProtectedRoute = protectedRoutes.some(route => 
    pathname === route || pathname.startsWith(route + '/')
  )
  
  // Check if the route is the auth page
  const isAuthRoute = pathname === '/auth' || pathname.startsWith('/auth/')
  
  // Get the token from cookies
  const accessToken = request.cookies.get('access_token')?.value
  const refreshToken = request.cookies.get('refresh_token')?.value
  
  // Debug logging
  console.log(`🔍 Middleware: ${pathname}`, {
    isProtectedRoute,
    isAuthRoute,
    hasAccessToken: !!accessToken,
    hasRefreshToken: !!refreshToken,
    cookies: request.cookies.getAll().map(c => c.name)
  })
  
  // Check if we have a valid token (either access or refresh token)
  const hasValidToken = accessToken || refreshToken
  
  // If it's a protected route and no valid token, redirect to auth
  if (isProtectedRoute && !hasValidToken) {
    console.log(`🔒 Redirecting to auth: ${pathname} requires authentication`)
    return NextResponse.redirect(new URL('/auth', request.url))
  }
  
  // If it's the auth page and user has valid token, redirect to home
  if (isAuthRoute && hasValidToken) {
    console.log(`🔄 Redirecting to home: user already authenticated`)
    return NextResponse.redirect(new URL('/', request.url))
  }

  if (pathname.startsWith('/admin')) {
    // Get the access token from cookies
    const accessToken = request.cookies.get('access_token')?.value
    
    if (!accessToken) {
      console.log(`🔒 No access token found for admin route: ${pathname}`)
      return NextResponse.redirect(new URL('/', request.url))
    }
    
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000'}/api/me`, {
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
    '/((?!api|_next/static|_next/image|favicon.ico|public).*)',
  ],
}
