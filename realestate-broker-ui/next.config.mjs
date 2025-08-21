const isStaticExport = process.env.NEXT_STATIC_EXPORT === 'true'

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    serverActions: { allowedOrigins: ['*'] },
  },
  ...(isStaticExport && { images: { unoptimized: true }, output: 'export' }),
}

export default nextConfig
