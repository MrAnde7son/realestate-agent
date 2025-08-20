import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Routes that require authentication
const protectedRoutes = [
  '/alerts',
  '/mortgage',
  '/reports',
  '/profile',
  '/settings'
]

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  
  // Check if the route requires authentication
  const isProtectedRoute = protectedRoutes.some(route => 
    pathname === route || pathname.startsWith(route + '/')
  )
  
  // Check if the route is the auth page
  const isAuthRoute = pathname === '/auth' || pathname.startsWith('/auth/')
  
  // Get the token from cookies or headers
  const token = request.cookies.get('access_token')?.value || 
                request.headers.get('authorization')?.replace('Bearer ', '')
  
  // If it's a protected route and no token, redirect to auth
  if (isProtectedRoute && !token) {
    return NextResponse.redirect(new URL('/auth', request.url))
  }
  
  // If it's the auth page and user has token, redirect to home
  if (isAuthRoute && token) {
    return NextResponse.redirect(new URL('/', request.url))
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
