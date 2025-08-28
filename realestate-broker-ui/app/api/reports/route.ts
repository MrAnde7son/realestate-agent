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

  // Helper to add a line to the PDF if the value exists
  const addLine = (label: string, value: any) => {
    if (value === undefined || value === null || value === '') return;
    // Format numbers with locale when possible
    let formatted: any = value;
    if (typeof value === 'number') {
      formatted = value.toLocaleString('he-IL');
    } else if (Array.isArray(value)) {
      formatted = value.map(v => (typeof v === 'number' ? v.toLocaleString('he-IL') : String(v))).join(', ');
    } else if (typeof value === 'boolean') {
      formatted = value ? 'כן' : 'לא';
    }
    doc.text(`${label}: ${formatted}`);
  };

  // Basic details
  addLine('כתובת', asset.address);
  addLine('עיר', asset.city);
  addLine('שכונה', asset.neighborhood);
  addLine('סוג', asset.type);
  addLine('מחיר', `₪${asset.price.toLocaleString('he-IL')}`);
  addLine('חדרים', asset.bedrooms);
  addLine('מקלחות', asset.bathrooms);
  addLine('מ"ר נטו', asset.netSqm ?? asset.area);
  addLine('מחיר למ"ר', asset.pricePerSqm ? `₪${asset.pricePerSqm.toLocaleString('he-IL')}` : undefined);
  addLine('יתרת זכויות', asset.remainingRightsSqm);
  addLine('תכנית', asset.program);
  addLine('היתר אחרון', asset.lastPermitQ);
  addLine('רמת רעש', asset.noiseLevel);
  addLine('תחרות 1 ק"מ', asset.competition1km);
  addLine('זונינג', asset.zoning);
  addLine('פער למחיר', asset.priceGapPct);
  addLine('טווח מחיר צפוי', asset.expectedPriceRange);
  addLine('מחיר מודל', asset.modelPrice ? `₪${asset.modelPrice.toLocaleString('he-IL')}` : undefined);
  addLine('רמת ביטחון', asset.confidencePct);
  addLine('תשואה', asset.capRatePct);
  addLine('הערכת שכירות', asset.rentEstimate ? `₪${asset.rentEstimate.toLocaleString('he-IL')}` : undefined);
  addLine('דגלי סיכון', asset.riskFlags && asset.riskFlags.length ? asset.riskFlags.join(', ') : undefined);
  addLine('מאפיינים', asset.features && asset.features.length ? asset.features.join(', ') : undefined);

  if (asset.contactInfo) {
    doc.moveDown().text('פרטי קשר:', { underline: true });
    addLine('סוכן', asset.contactInfo.agent);
    addLine('טלפון', asset.contactInfo.phone);
    addLine('אימייל', asset.contactInfo.email);
  }

  if (asset.documents && asset.documents.length) {
    doc.moveDown().text('מסמכים:', { underline: true });
    asset.documents.forEach((d: any) => {
      addLine('-', `${d.name}${d.type ? ` (${d.type})` : ''}`);
    });
  }

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
