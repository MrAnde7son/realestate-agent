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
            "https://nadlaner.vercel.app",
            "https://app.nadlaner.com",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
          ].filter(Boolean)
        )
      ),
    },
  },

  async rewrites() {
    const backend = (process.env.BACKEND_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')
    return [
      { source: '/api/:path*', destination: `${backend}/api/:path*` },
    ]
  },

  images: {
    remotePatterns: [
      { protocol: "https", hostname: "api.nadlaner.com" },
      { protocol: "https", hostname: "backend-django-2cpe.onrender.com" },
      { protocol: "https", hostname: "cdn.yad2.treedis.com" },
      { protocol: "https", hostname: "img.yad2.co.il" },
      { protocol: "https", hostname: "images-processor.madlan.co.il" },
      { protocol: "https", hostname: "images2.madlan.co.il" },
      { protocol: "http", hostname: "127.0.0.1" },
      { protocol: "http", hostname: "localhost" },
    ],
    qualities: [75, 85],
  },

  env: {
    BACKEND_URL: process.env.BACKEND_URL || "http://127.0.0.1:8000",
  },
};

export default nextConfig;
