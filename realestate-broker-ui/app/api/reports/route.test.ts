import { POST, GET } from './route';
import { reports } from '@/lib/reports';
import { listings } from '@/lib/data';
import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';

describe('reports API', () => {
  it('creates a new report', async () => {
    const initial = reports.length;
    const req = new Request('http://localhost/api/reports', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ listingId: listings[0].id }),
    });
    const res = await POST(req);
    const data = await res.json();
    expect(res.status).toBe(201);
    expect(data.report.listingId).toBe(listings[0].id);
    const filePath = path.join(process.cwd(), 'public', 'reports', data.report.filename);
    expect(fs.existsSync(filePath)).toBe(true);
    fs.unlinkSync(filePath);
    reports.pop();
    expect(reports.length).toBe(initial);
  });

  it('validates listingId', async () => {
    const req = new Request('http://localhost/api/reports', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    const res = await POST(req);
    expect(res.status).toBe(400);
  });

  it('returns 404 for unknown listing', async () => {
    const req = new Request('http://localhost/api/reports', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ listingId: 'missing' }),
    });
    const res = await POST(req);
    expect(res.status).toBe(404);
  });

  it('lists reports', async () => {
    const res = await GET(new Request('http://localhost/api/reports'));
    const data = await res.json();
    expect(Array.isArray(data.reports)).toBe(true);
  });
});
