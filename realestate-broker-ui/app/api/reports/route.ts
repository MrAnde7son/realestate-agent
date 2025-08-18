import { NextResponse } from 'next/server';
import PDFDocument from 'pdfkit';
import fs from 'fs';
import path from 'path';
import { reports, type Report } from '@/lib/reports';
import { listings } from '@/lib/data';

export async function GET(req: Request) {
  return NextResponse.json({ reports });
}

export async function POST(req: Request) {
  const { listingId } = await req.json();
  const listing = listings.find(l => l.id === listingId);
  if (!listing) {
    return NextResponse.json({ error: 'Listing not found' }, { status: 404 });
  }

  const id = `r${reports.length + 1}`;
  const filename = `${id}.pdf`;
  const dir = path.join(process.cwd(), 'public', 'reports');
  fs.mkdirSync(dir, { recursive: true });
  const filePath = path.join(dir, filename);

  const doc = new PDFDocument();
  const stream = fs.createWriteStream(filePath);
  doc.pipe(stream);
  doc.fontSize(20).text('דו"ח נכס', { align: 'center' });
  doc.moveDown();
  doc.fontSize(12).text(`כתובת: ${listing.address}`);
  doc.text(`מחיר: ₪${listing.price.toLocaleString('he-IL')}`);
  doc.text(`חדרים: ${listing.bedrooms}`);
  doc.text(`מקלחות: ${listing.bathrooms}`);
  doc.text(`מ"ר: ${listing.area}`);
  doc.end();
  await new Promise<void>((resolve) => stream.on('finish', () => resolve()));

  const report: Report = {
    id,
    listingId,
    address: listing.address,
    filename,
    createdAt: new Date().toISOString(),
  };
  reports.push(report);
  return NextResponse.json({ report }, { status: 201 });
}
