import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { z } from 'zod'
import { validateToken } from '@/lib/token-utils'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

const formSchema = z.object({
  dealId: z.coerce.number({ invalid_type_error: 'dealId must be a number' }),
  assetId: z.coerce.number({ invalid_type_error: 'assetId must be a number' }),
  kind: z.enum(['legal', 'appraisal', 'architect', 'mortgage', 'generic']).default('generic'),
  visibility: z.enum(['deal', 'buyer_side', 'seller_side']).default('deal'),
  title: z.string().min(1).max(255).optional(),
})

export async function POST(request: Request) {
  const formData = await request.formData()
  const file = formData.get('file')

  if (!(file instanceof Blob)) {
    return NextResponse.json({ error: 'File is required' }, { status: 400 })
  }

  const rawPayload = {
    dealId: formData.get('deal_id') ?? formData.get('dealId'),
    assetId: formData.get('asset_id') ?? formData.get('assetId'),
    kind: (formData.get('kind') ?? 'generic') as string,
    visibility: (formData.get('visibility') ?? 'deal') as string,
    title: (formData.get('title') ?? '').toString().trim() || undefined,
  }

  const parsed = formSchema.safeParse(rawPayload)
  if (!parsed.success) {
    return NextResponse.json({ error: 'Validation failed', details: parsed.error.flatten() }, { status: 400 })
  }

  const { dealId, assetId, kind, visibility, title } = parsed.data

  const cookieStore = await cookies()
  let token = cookieStore.get('access_token')?.value

  if (!token) {
    const authHeader = request.headers.get('authorization')
    if (authHeader?.startsWith('Bearer ')) {
      token = authHeader.slice(7)
    }
  }

  const tokenValidation = validateToken(token)
  if (!tokenValidation.isValid) {
    const response = NextResponse.json({ error: 'Unauthorized - Token expired or invalid' }, { status: 401 })
    response.cookies.delete('access_token')
    response.cookies.delete('refresh_token')
    return response
  }

  const filename = file instanceof File ? file.name : 'document'
  const assetUploadForm = new FormData()
  assetUploadForm.append('file', file, filename)
  assetUploadForm.append('document_type', 'other')
  assetUploadForm.append('title', title || filename || 'מסמך')

  try {
    const uploadResponse = await fetch(`${BACKEND_URL}/api/assets/${assetId}/documents/upload`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: assetUploadForm,
    })

    const uploadText = await uploadResponse.text()
    let uploadData: any = null
    if (uploadText) {
      try {
        uploadData = JSON.parse(uploadText)
      } catch (error) {
        console.warn('Failed to parse asset document upload response:', error)
      }
    }

    if (!uploadResponse.ok) {
      return NextResponse.json(uploadData || { error: 'Failed to upload file' }, { status: uploadResponse.status })
    }

    const uploadedDoc = uploadData?.doc || uploadData
    const downloadUrl: string = uploadedDoc?.url || uploadedDoc?.file_url

    if (!downloadUrl) {
      return NextResponse.json({ error: 'Upload succeeded but no download URL returned' }, { status: 502 })
    }

    const absoluteUrl = downloadUrl.startsWith('http') ? downloadUrl : `${BACKEND_URL}${downloadUrl}`

    const createPayload = {
      deal: dealId,
      asset: assetId,
      kind,
      title: title || uploadedDoc?.title || filename,
      storage_url: absoluteUrl,
      visibility_scope: visibility,
    }

    const createResponse = await fetch(`${BACKEND_URL}/api/deal-workspace/documents`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(createPayload),
    })

    const createText = await createResponse.text()
    let createdDoc: any = null
    if (createText) {
      try {
        createdDoc = JSON.parse(createText)
      } catch (error) {
        console.warn('Failed to parse deal workspace document response:', error)
      }
    }

    if (!createResponse.ok) {
      return NextResponse.json(createdDoc || { error: 'Failed to register document' }, { status: createResponse.status })
    }

    return NextResponse.json({ document: createdDoc, assetDocument: uploadedDoc }, { status: 201 })
  } catch (error) {
    console.error('Failed to upload deal workspace document:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
