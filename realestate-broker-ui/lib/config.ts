export const siteConfig = {
  name: "Real Estate Home",
  description: "Professional real estate management platform",
  url: "https://realestate-agent.vercel.app",
  author: "Real Estate Agent",
  version: "1.0.0",
}

const apiRoot = process.env.NEXT_PUBLIC_API_URL || ''
export const API_BASE = apiRoot.endsWith('/api')
  ? apiRoot
  : `${apiRoot.replace(/\/$/, '')}/api`
