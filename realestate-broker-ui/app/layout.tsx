import type { Metadata } from 'next'
import { ReactNode } from 'react'
import { ThemeProvider } from '@/components/theme-provider'
import { AuthProvider } from '@/lib/auth-context'
import './globals.css'

export const metadata: Metadata = { 
  title: 'נדל״נר - נדל״ן חכם לשמאים, מתווכים ומשקיעים',
  description: 'פלטפורמה חכמה מבוססת בינה מלאכותית לניהול נכסים עבור מתווכים, שמאים ומשקיעים',
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="he" dir="rtl" suppressHydrationWarning>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
        <link rel="icon" href="/brand/favicon.svg" type="image/svg+xml" />
        <link rel="alternate icon" href="/brand/favicon-32.png" sizes="32x32" />
        <link rel="apple-touch-icon" href="/brand/favicon-192.png" />
      </head>
      <body className="min-h-[100dvh] bg-background font-sans antialiased">
        <ThemeProvider
          attribute="class"
          defaultTheme="light"
          enableSystem
          disableTransitionOnChange
        >
          <AuthProvider>
            {children}
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
