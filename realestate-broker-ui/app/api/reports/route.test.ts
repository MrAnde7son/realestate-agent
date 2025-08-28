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
    const req = new Request('http://localhost/api/reports', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ assetId: assets[0].id }),
    });
    
    const res = await POST(req);
    const data = await res.json();
    
    // Check basic response structure
    expect(res.status).toBe(201);
    expect(data.report.assetId).toBe(assets[0].id);
    expect(data.report.filename).toBeDefined();
    
    // If backend is available, check for backend-specific fields
    if (data.report.status) {
      expect(data.report.status).toBe('completed');
      expect(data.report.pages).toBeGreaterThan(0);
      expect(data.report.fileSize).toBeGreaterThan(0);
    } else {
      // Local fallback - check for local-specific fields
      expect(data.report.createdAt).toBeDefined();
      expect(data.report.address).toBeDefined();
    }
  });

  it('handles missing assetId gracefully', async () => {
    const req = new Request('http://localhost/api/reports', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    
    const res = await POST(req);
    expect(res.status).toBe(400);
    
    const data = await res.json();
    expect(data.error).toBe('Invalid assetId');
  });

  it('handles invalid assetId gracefully', async () => {
    const req = new Request('http://localhost/api/reports', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ assetId: 'invalid' }),
    });
    
    const res = await POST(req);
    expect(res.status).toBe(400);
    
    const data = await res.json();
    expect(data.error).toBe('Invalid assetId');
  });

  it('lists reports', async () => {
    const res = await GET(new Request('http://localhost/api/reports'));
    const data = await res.json();
    expect(Array.isArray(data.reports)).toBe(true);
  });
});
