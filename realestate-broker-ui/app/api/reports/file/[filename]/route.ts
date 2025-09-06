import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';

export async function GET(
  req: Request,
  { params }: { params: { filename: string } }
) {
  const { filename } = params;
  try {
    const res = await fetch(`${BACKEND_URL}/api/reports/file/${filename}`, { cache: 'no-store' });
    if (res.ok) {
      const buffer = await res.arrayBuffer();
      return new NextResponse(buffer, {
        status: res.status,
        headers: {
          'Content-Type': res.headers.get('Content-Type') || 'application/pdf',
        },
      });
    }
  } catch (err) {
    console.error('Backend report fetch failed:', err);
  }

  try {
    const filePath = path.join(process.cwd(), 'public', 'reports', filename);
    const file = fs.readFileSync(filePath);
    return new NextResponse(file, {
      status: 200,
      headers: { 'Content-Type': 'application/pdf' },
    });
  } catch (err) {
    return NextResponse.json({ error: 'Report not found' }, { status: 404 });
  }
}
