import { NextResponse } from 'next/server'
import { promises as fs } from 'fs'
import path from 'path'
import { listings } from '@/lib/data'

export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const formData = await req.formData()
  const file = formData.get('file') as File | null
  const type = formData.get('type') as string | null
  if (!file || !type) {
    return new NextResponse('Missing file or type', { status: 400 })
  }

  const bytes = await file.arrayBuffer()
  const buffer = Buffer.from(bytes)
  const uploadsDir = path.join(process.cwd(), 'public', 'uploads', id)
  await fs.mkdir(uploadsDir, { recursive: true })
  const filePath = path.join(uploadsDir, file.name)
  await fs.writeFile(filePath, buffer)
  const doc = { name: file.name, url: `/uploads/${id}/${file.name}`, type }
  const listing = listings.find(l => l.id === id)
  if (listing) {
    listing.documents = [...(listing.documents || []), doc]
  }
  return NextResponse.json({ doc })
}
