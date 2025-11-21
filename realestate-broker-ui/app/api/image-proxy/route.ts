import { NextResponse } from 'next/server'
import https from 'https'
import http from 'http'

// Create an agent that accepts self-signed certificates (development only)
const isDevelopment = process.env.NODE_ENV === 'development'
const httpsAgent = isDevelopment
  ? new https.Agent({
      rejectUnauthorized: false, // Accept self-signed certificates in development
    })
  : undefined

// Helper function to fetch image using Node.js https/http modules
function fetchImageWithAgent(url: URL): Promise<{ buffer: Buffer; contentType: string }> {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: url.hostname,
      port: url.port || (url.protocol === 'https:' ? 443 : 80),
      path: url.pathname + url.search,
      method: 'GET',
      headers: {
        'User-Agent': 'RealEstateAgent/1.0',
        'Accept': 'image/png,image/jpeg,image/webp,image/gif,*/*',
      },
      ...(url.protocol === 'https:' && httpsAgent ? { agent: httpsAgent } : {}),
    }

    const client = url.protocol === 'https:' ? https : http
    const req = client.request(options, (res) => {
      const chunks: Buffer[] = []
      res.on('data', (chunk) => chunks.push(chunk))
      res.on('end', () => {
        const buffer = Buffer.concat(chunks)
        const contentType = res.headers['content-type'] || 'image/jpeg'
        resolve({ buffer, contentType })
      })
    })

    req.on('error', (error) => {
      reject(error)
    })

    req.end()
  })
}

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const imageUrl = searchParams.get('url')

    // Validate URL parameter
    if (!imageUrl) {
      return NextResponse.json(
        { error: 'Missing required parameter: url' },
        { status: 400 }
      )
    }

    // Validate that the URL is from an allowed domain
    const allowedDomains = [
      'img.yad2.co.il',
      'cdn.yad2.treedis.com',
      'api.nadlaner.com',
      'backend-django-2cpe.onrender.com',
      "images-processor.madlan.co.il",
      "images2.madlan.co.il"
    ]

    let url: URL
    try {
      url = new URL(imageUrl)
    } catch {
      return NextResponse.json(
        { error: 'Invalid URL format' },
        { status: 400 }
      )
    }

    // Check if domain is allowed
    if (!allowedDomains.some(domain => url.hostname === domain || url.hostname.endsWith(`.${domain}`))) {
      return NextResponse.json(
        { error: 'Domain not allowed' },
        { status: 403 }
      )
    }

    // Fetch the image using Node.js https/http with custom agent
    const { buffer, contentType } = await fetchImageWithAgent(url)

    // Return the image with appropriate headers
    return new NextResponse(new Uint8Array(buffer), {
      status: 200,
      headers: {
        'Content-Type': contentType,
        'Cache-Control': 'public, max-age=86400', // Cache for 24 hours
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET',
        'Access-Control-Allow-Headers': 'Content-Type',
      },
    })
  } catch (error) {
    console.error('Image proxy error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

// Handle preflight requests
export async function OPTIONS(_request: Request) {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  })
}

