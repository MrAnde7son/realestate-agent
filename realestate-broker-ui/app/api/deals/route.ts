import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { z } from 'zod'
import { validateToken } from '@/lib/token-utils'
import { DEAL_SUMMARIES_MOCK } from '@/app/assets/[id]/deal/mock-data'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

const createDealSchema = z.object({
  assetId: z.number({ invalid_type_error: 'assetId must be a number' }),
  stage: z
    .enum(['discovery', 'negotiation', 'legal', 'financing', 'closing', 'abandoned'])
    .default('discovery'),
  confidentialityLevel: z.enum(['standard', 'restricted', 'internal']).default('standard'),
  parties: z
    .array(
      z.object({
        userId: z.number().optional(),
        role: z.string(),
        side: z.string(),
        externalContact: z
          .object({
            name: z.string().optional(),
            email: z.string().optional(),
            phone: z.string().optional(),
          })
          .optional(),
      })
    )
    .default([]),
})

type BackendDeal = {
  id: number
  asset: number
  stage: string
  deal_lead: number | null
  confidentiality_level: string
  created_at: string
  updated_at: string
  party_roles: unknown[]
  asset_summary?: unknown
}

export async function GET(request: Request) {
  const cookieStore = await cookies()
  const token = cookieStore.get('access_token')?.value
  const search = (() => {
    try {
      const url = new URL(request.url)
      return url.search
    } catch (error) {
      console.warn('Failed to parse deals request URL:', error)
      return ''
    }
  })()

  try {
    const res = await fetch(`${BACKEND_URL}/api/deal-workspace/deals${search}`, {
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    })

    if (!res.ok) {
      const message = await res.text()
      console.warn('Backend deals API returned error:', res.status, message)
      return NextResponse.json(
        {
          deals: DEAL_SUMMARIES_MOCK,
          fallback: true,
          error: message || `Failed to load deals (status ${res.status})`,
        },
        { status: 200 }
      )
    }

    const data: BackendDeal[] = await res.json()
    return NextResponse.json({ deals: data })
  } catch (error) {
    console.error('Failed to fetch deals from backend:', error)
    return NextResponse.json(
      {
        deals: DEAL_SUMMARIES_MOCK,
        fallback: true,
        error: 'Unable to fetch deals',
      },
      { status: 200 }
    )
  }
}

export async function POST(request: Request) {
  const body = await request.json().catch(() => null)
  if (!body) {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 })
  }

  const parsed = createDealSchema.safeParse(body)
  if (!parsed.success) {
    return NextResponse.json(
      { error: 'Validation failed', details: parsed.error.flatten() },
      { status: 400 }
    )
  }

  const cookieStore = await cookies()
  const token = cookieStore.get('access_token')?.value
  const validation = validateToken(token)
  if (!validation.isValid) {
    const response = NextResponse.json({ error: 'Unauthorized - Token expired or invalid' }, { status: 401 })
    response.cookies.delete('access_token')
    response.cookies.delete('refresh_token')
    return response
  }

  const { assetId, stage, confidentialityLevel, parties } = parsed.data
  const payload = {
    stage,
    confidentiality_level: confidentialityLevel,
    parties: parties.map((party) => ({
      user_id: party.userId,
      role: party.role,
      side: party.side,
      external_contact_json: party.externalContact ?? {},
    })),
  }

  try {
    const res = await fetch(`${BACKEND_URL}/api/deal-workspace/deals/${assetId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    })

    const text = await res.text()
    let data: BackendDeal | null = null
    if (text) {
      try {
        data = JSON.parse(text)
      } catch (error) {
        console.warn('Failed to parse backend deal create response:', error)
      }
    }

    if (!res.ok) {
      return NextResponse.json({ error: data || text || 'Failed to create deal' }, { status: res.status })
    }

    return NextResponse.json({ deal: data }, { status: res.status })
  } catch (error) {
    console.error('Failed to create deal:', error)
    return NextResponse.json({ error: 'Unable to create deal' }, { status: 500 })
  }
}
