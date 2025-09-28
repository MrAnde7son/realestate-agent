/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  trailingSlash: false, // Disable automatic trailing slash redirects
  experimental: {
    serverActions: { allowedOrigins: ['*'] },
  },
  env: {
    BACKEND_URL: process.env.BACKEND_URL || 'http://127.0.0.1:8000',
  },
}

export default nextConfig
