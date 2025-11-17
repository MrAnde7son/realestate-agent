import type { Metadata } from 'next'
import { ReactNode } from 'react'
import Script from 'next/script'
import { ThemeProvider } from '@/components/theme-provider'
import { AuthProvider } from '@/lib/auth-context'
import { AnalyticsProvider } from '@/components/analytics-provider'
import { Toaster } from '@/components/ui/toaster'
import { ConfirmationDialog } from '@/components/ui/confirmation-dialog'
import { AgentChat } from '@/components/AgentChat'
import { Analytics } from '@vercel/analytics/react'   
import { SpeedInsights } from '@vercel/speed-insights/next' 
import { ConfirmProvider } from '@/hooks/use-confirm'
import './globals.css'

export const metadata: Metadata = { 
  title: 'נדל״נר - נדל״ן חכם לאנשים פרטיים ומתווכים',
  description: 'פלטפורמה חכמה מבוססת בינה מלאכותית לניהול נכסים עבור אנשים פרטיים ומתווכים',
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
      <Script
        src="https://www.googletagmanager.com/gtag/js?id=G-Y7L94EMRRG"
        strategy="afterInteractive"
      />
      <Script id="google-analytics" strategy="afterInteractive">
        {`
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());
          gtag('config', 'G-Y7L94EMRRG');
        `}
      </Script>
      <body className="min-h-[100dvh] bg-background font-sans antialiased">
        <ThemeProvider
          attribute="class"
          defaultTheme="light"
          enableSystem
          disableTransitionOnChange
        >
          <AuthProvider>
            <AnalyticsProvider>
              <ConfirmProvider>
                {children}
                <Toaster />
                <ConfirmationDialog />
                <AgentChat fetchRecommendationsFromAPI={true} />
              </ConfirmProvider>
            </AnalyticsProvider>
          </AuthProvider>
        </ThemeProvider>
        <Analytics /> 
        <SpeedInsights />
      </body>
    </html>
  )
}
