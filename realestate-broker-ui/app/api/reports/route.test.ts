import { POST, GET } from './route';
import { reports } from '@/lib/reports';
import { assets } from '@/lib/data';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';

// Mock fs module for tests
vi.mock('fs', () => ({
  default: {
    existsSync: vi.fn(),
    mkdirSync: vi.fn(),
    writeFileSync: vi.fn(),
    unlinkSync: vi.fn(),
  }
}));

// Mock path module
vi.mock('path', () => ({
  default: {
    join: vi.fn((...args) => args.join('/')),
  }
}));

describe('reports API', () => {
  beforeEach(() => {
    // Reset mocks before each test
    vi.clearAllMocks();
    
    // Mock fs.existsSync to return true for directory check
    vi.mocked(fs.existsSync).mockReturnValue(true);
    
    // Mock fs.mkdirSync to do nothing
    vi.mocked(fs.mkdirSync).mockImplementation(() => undefined);
    
    // Mock fs.writeFileSync to do nothing
    vi.mocked(fs.writeFileSync).mockImplementation(() => undefined);
    
    // Mock fs.unlinkSync to do nothing
    vi.mocked(fs.unlinkSync).mockImplementation(() => undefined);
  });

  afterEach(() => {
    // Clean up after each test
    vi.restoreAllMocks();
  });

  it('creates a new report', async () => {
    const initial = reports.length;
    const req = new Request('http://localhost/api/reports', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ assetId: assets[0].id }),
    });
    
    const res = await POST(req);
    const data = await res.json();
    
    // In CI environment, we expect the local fallback to work
    expect(res.status).toBe(201);
    expect(data.report.assetId).toBe(assets[0].id);
    expect(data.report.filename).toBeDefined();
    
    // Verify that the report was added to local reports
    expect(reports.length).toBe(initial + 1);
    
    // Clean up
    reports.pop();
    expect(reports.length).toBe(initial);
  });

  it('lists reports', async () => {
    const res = await GET(new Request('http://localhost/api/reports'));
    const data = await res.json();
    expect(Array.isArray(data.reports)).toBe(true);
  });

  it('handles missing assetId gracefully', async () => {
    const req = new Request('http://localhost/api/reports', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    
    const res = await POST(req);
    expect(res.status).toBe(400);
  });

  it('handles invalid assetId gracefully', async () => {
    const req = new Request('http://localhost/api/reports', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ assetId: 99999 }),
    });
    
    const res = await POST(req);
    expect(res.status).toBe(404);
  });
});
