/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  trailingSlash: false, // Disable automatic trailing slash redirects
  experimental: {
    serverActions: {
      allowedOrigins: Array.from(
        new Set(
          [
            process.env.FRONTEND_URL,
            process.env.NEXT_PUBLIC_SITE_URL,
            'https://realestate-agent.vercel.app',
            'http://localhost:3000',
            'http://127.0.0.1:3000',
          ].filter(Boolean)
        )
      ),
    },
  },
  env: {
    BACKEND_URL: process.env.BACKEND_URL || 'http://127.0.0.1:8000',
  },
}

export default nextConfig
