import './globals.css'
import { ReactNode } from 'react'
import Providers from '@/components/providers'
import { Heebo } from 'next/font/google'

const heebo = Heebo({ 
  subsets: ['hebrew'],
  weight: ['500', '700'],
  display: 'swap',
  variable: '--font-heebo'
})

export const metadata = { 
  title: 'נדל״נר', 
  description: 'נדל״ן חכם לשמאים, מתווכים ומשקיעים' 
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="he" dir="rtl" suppressHydrationWarning className={heebo.variable}>
      <head>
        <link rel="icon" href="/brand/favicon.svg" type="image/svg+xml" />
        <link rel="alternate icon" href="/brand/favicon-32.png" sizes="32x32" />
        <link rel="apple-touch-icon" href="/brand/favicon-192.png" />
      </head>
      <body className="min-h-screen bg-background font-sans antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
