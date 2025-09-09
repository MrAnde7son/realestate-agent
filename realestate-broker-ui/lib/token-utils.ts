/**
 * Shared token validation utilities for both client and server-side use
 */

export interface TokenValidationResult {
  isValid: boolean
  isExpired: boolean
  needsRefresh: boolean
  error?: string
}

/**
 * Check if a JWT token is expired
 */
export function isTokenExpired(token: string): boolean {
  try {
    // JWT tokens have 3 parts separated by dots
    const parts = token.split('.')
    if (parts.length !== 3) return true

    // Decode the payload (second part)
    const payload = JSON.parse(atob(parts[1]))
    const currentTime = Math.floor(Date.now() / 1000)
    
    // Check if token is expired (exp claim is in seconds)
    return payload.exp < currentTime
  } catch (error) {
    console.error('Error checking token expiration:', error)
    return true // Assume expired if we can't parse
  }
}

/**
 * Validate a token and return detailed validation result
 */
export function validateToken(token: string | null | undefined): TokenValidationResult {
  if (!token) {
    return {
      isValid: false,
      isExpired: false,
      needsRefresh: false,
      error: 'No token provided'
    }
  }

  const isExpired = isTokenExpired(token)
  
  return {
    isValid: !isExpired,
    isExpired,
    needsRefresh: isExpired,
    error: isExpired ? 'Token expired' : undefined
  }
}

/**
 * Extract token from Authorization header
 */
export function extractTokenFromHeader(authHeader: string | null): string | null {
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return null
  }
  return authHeader.substring(7)
}

/**
 * Get token expiration time in milliseconds
 */
export function getTokenExpirationTime(token: string): number | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null

    const payload = JSON.parse(atob(parts[1]))
    return payload.exp * 1000 // Convert to milliseconds
  } catch (error) {
    console.error('Error getting token expiration time:', error)
    return null
  }
}

/**
 * Get time until token expires in milliseconds
 */
export function getTimeUntilExpiration(token: string): number | null {
  const expirationTime = getTokenExpirationTime(token)
  if (!expirationTime) return null
  
  return Math.max(0, expirationTime - Date.now())
}
