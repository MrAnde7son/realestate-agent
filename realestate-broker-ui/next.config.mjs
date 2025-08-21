/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: { unoptimized: true },
  output: 'export',
  experimental: {
    serverActions: { allowedOrigins: ['*'] },
  },
};
export default nextConfig;
