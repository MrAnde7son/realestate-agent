import { cookies } from 'next/headers'

export async function getAccessToken(request: Request): Promise<string | null> {
  const authHeader = request.headers.get('authorization')
  if (authHeader?.toLowerCase().startsWith('bearer ')) {
    const token = authHeader.slice(7).trim()
    if (token) {
      return token
    }
  }

  const header = request.headers.get('cookie')
  if (header) {
    const tokenFromHeader = header
      .split(';')
      .map(part => part.trim())
      .find(part => part.startsWith('access_token='))

    if (tokenFromHeader) {
      return decodeURIComponent(tokenFromHeader.split('=').slice(1).join('='))
    }
  }

  try {
    const cookieStore = await cookies()
    return cookieStore.get('access_token')?.value ?? null
  } catch {
    return null
  }
}
