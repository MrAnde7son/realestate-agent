import './globals.css'
import { ReactNode } from 'react'
import { ThemeProvider } from '@/components/theme-provider'

export const metadata = { 
  title: 'נדל״נר', 
  description: 'נדל״ן חכם לשמאים, מתווכים ומשקיעים' 
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="he" dir="rtl" suppressHydrationWarning>
      <body className="min-h-screen bg-background font-sans antialiased">
        <ThemeProvider
          attribute="class"
          defaultTheme="light"
          enableSystem
          disableTransitionOnChange
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}
