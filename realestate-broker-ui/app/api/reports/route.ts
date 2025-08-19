import { NextResponse } from 'next/server';
import PDFDocument from 'pdfkit';
import fs from 'fs';
import { promises as fsPromises } from 'fs';
import path from 'path';
import { reports, type Report } from '@/lib/reports';
import {
  listings,
  appraisalByListing,
  compsByListing,
  rightsByListing,
} from '@/lib/data';

export async function GET(req: Request) {
  return NextResponse.json({ reports });
}

export async function POST(req: Request) {
  const { listingId } = await req
    .json()
    .catch(() => ({} as Record<string, string>));
  if (!listingId) {
    return NextResponse.json({ error: 'listingId is required' }, { status: 400 });
  }
  const listing = listings.find(l => l.id === listingId);
  if (!listing) {
    return NextResponse.json({ error: 'Listing not found' }, { status: 404 });
  }

  const id = `r${reports.length + 1}`;
  const filename = `${id}.pdf`;
  const dir = path.join(process.cwd(), 'public', 'reports');
  await fsPromises.mkdir(dir, { recursive: true });
  const filePath = path.join(dir, filename);

  const appraisal = appraisalByListing(listingId);
  const comps = compsByListing(listingId);
  const rights = rightsByListing(listingId);

  const doc = new PDFDocument({ compress: false });
  const stream = fs.createWriteStream(filePath);
  doc.pipe(stream);

  // Title
  doc.fontSize(20).text('דו"ח נכס', { align: 'center' });
  doc.moveDown();

  // ניתוח כללי
  doc.fontSize(16).text('ניתוח כללי');
  doc.fontSize(12)
    .text(`כתובת: ${listing.address}`)
    .text(`מחיר: ₪${listing.price.toLocaleString('he-IL')}`)
    .text(`חדרי שינה: ${listing.bedrooms}`)
    .text(`חדרי רחצה: ${listing.bathrooms}`)
    .text(`שטח: ${listing.area} מ'ר`);
  doc.moveDown();

  // עסקאות להשוואה
  doc.fontSize(16).text('עסקאות להשוואה');
  doc.fontSize(12);
  comps.forEach((c, i) => {
    doc.text(
      `${i + 1}. ${c.address} – ₪${c.price.toLocaleString('he-IL')} (${c.area} מ'ר, ₪${c.pricePerSqm}/מ'ר) - ${c.date}`
    );
  });
  doc.moveDown();

  // שומות באזור
  doc.fontSize(16).text('שומות באזור');
  doc.fontSize(12)
    .text(`שווי שוק: ₪${appraisal.marketValue.toLocaleString('he-IL')}`)
    .text(`שווי שמאי: ₪${appraisal.appraisedValue.toLocaleString('he-IL')}`)
    .text(`שמאי: ${appraisal.appraiser} (${appraisal.date})`)
    .text(`הערות: ${appraisal.notes}`);
  doc.moveDown();

  // זכויות בנייה
  doc.fontSize(16).text('זכויות בנייה');
  doc.fontSize(12)
    .text(rights.buildingRights)
    .text(`ייעוד קרקע: ${rights.landUse}`)
    .text(`מגבלות: ${rights.restrictions.join(', ')}`)
    .text(`היתרים: ${rights.permits.join(', ')}`)
    .text(`עדכון אחרון: ${rights.lastUpdate}`);

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
