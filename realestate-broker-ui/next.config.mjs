/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    serverActions: { allowedOrigins: ['*'] },
  },
  env: {
    BACKEND_URL: process.env.BACKEND_URL,
  },
}

export default nextConfig
