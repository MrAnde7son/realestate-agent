import { NextResponse } from 'next/server';
import PDFDocument from 'pdfkit';
import fs from 'fs';
import path from 'path';
import { reports, type Report } from '@/lib/reports';
import { assets } from '@/lib/data';

const BACKEND_URL = process.env.BACKEND_URL;

export async function GET(req: Request) {
  if (BACKEND_URL) {
    try {
      const res = await fetch(`${BACKEND_URL}/api/reports`, { cache: 'no-store' });
      if (res.ok) {
        const data = await res.json();
        const backendReports = data.reports || [];
        return NextResponse.json({ reports: [...backendReports, ...reports] });
      }
    } catch (err) {
      console.error('Backend reports fetch failed:', err);
    }
  }
  return NextResponse.json({ reports });
}

export async function POST(req: Request) {
  const body = await req.json();
  const assetId = Number(body.assetId);

  if (BACKEND_URL) {
    try {
      const res = await fetch(`${BACKEND_URL}/api/reports`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ assetId }),
      });
      if (res.ok) {
        const data = await res.json();
        return NextResponse.json(data, { status: res.status });
      }
    } catch (err) {
      console.error('Backend report creation failed:', err);
    }
  }

  const asset = assets.find(l => l.id === assetId);
if (!asset) {
  return NextResponse.json({ error: 'Asset not found' }, { status: 404 });
}

  const id = reports.length + 1;
  const filename = `r${id}.pdf`;
  const dir = path.join(process.cwd(), 'public', 'reports');
  fs.mkdirSync(dir, { recursive: true });
  const filePath = path.join(dir, filename);

  const doc = new PDFDocument();
  const stream = fs.createWriteStream(filePath);
  doc.pipe(stream);

  const fontPath = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';
  if (fs.existsSync(fontPath)) {
    doc.font(fontPath);
  }

  doc.fontSize(20).text('דו"ח נכס', { align: 'center' });
  doc.moveDown();
      doc.fontSize(12).text(`כתובת: ${asset.address}`);
    doc.text(`מחיר: ₪${asset.price.toLocaleString('he-IL')}`);
    doc.text(`חדרים: ${asset.bedrooms}`);
    doc.text(`מקלחות: ${asset.bathrooms}`);
    doc.text(`מ"ר: ${asset.area}`);
  doc.end();
  await new Promise<void>((resolve) => stream.on('finish', () => resolve()));

  const report: Report = {
    id,
    assetId,
    address: asset.address,
    filename,
    createdAt: new Date().toISOString(),
  };
  reports.push(report);
  return NextResponse.json({ report }, { status: 201 });
}
