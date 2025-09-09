import { POST, GET } from './route';
import { reports } from '@/lib/reports';
import { assets } from '@/lib/data';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';

// Create a valid JWT token for testing (expires in 1 hour)
const createMockJWT = () => {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }))
  const payload = btoa(JSON.stringify({ 
    exp: Math.floor(Date.now() / 1000) + 3600, // 1 hour from now
    iat: Math.floor(Date.now() / 1000),
    sub: 'test-user'
  }))
  const signature = 'mock-signature'
  return `${header}.${payload}.${signature}`
}

// Mock cookies
vi.mock('next/headers', () => ({
  cookies: vi.fn(() => ({
    get: vi.fn((name: string) => {
      if (name === 'access_token') {
        return { value: createMockJWT() }
      }
      return undefined
    })
  }))
}))

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
    // Mock the backend fetch call
    const fetchMock = vi.spyOn(global, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ 
        id: 1, 
        asset_id: assets[0].id, 
        filename: 'test-report.pdf',
        status: 'completed',
        pages: 5,
        file_size: 1024
      }), { status: 201 })
    );

    const req = new Request('http://127.0.0.1/api/reports', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ assetId: assets[0].id }),
    });
    
    const res = await POST(req);
    const data = await res.json();

    fetchMock.mockRestore();
    
    // Check basic response structure
    expect(res.status).toBe(201);
    expect(data.id).toBeDefined();
    expect(data.asset_id).toBe(assets[0].id);
    expect(data.filename).toBeDefined();
    
    // If backend is available, check for backend-specific fields
    if (data.status) {
      expect(data.status).toBe('completed');
      expect(data.pages).toBeGreaterThan(0);
      expect(data.file_size).toBeGreaterThan(0);
    } else {
      // Local fallback - check for local-specific fields
      expect(data.createdAt).toBeDefined();
      expect(data.address).toBeDefined();
    }
  });

  it('handles missing assetId gracefully', async () => {
    const req = new Request('http://127.0.0.1/api/reports', {
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
    const req = new Request('http://127.0.0.1/api/reports', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ assetId: 'invalid' }),
    });
    
    const res = await POST(req);
    expect(res.status).toBe(400);
    
    const data = await res.json();
    expect(data.error).toBe('Invalid assetId');
  });

  it('falls back to local data when backend returns 404', async () => {
    const fetchMock = vi.spyOn(global, 'fetch').mockResolvedValueOnce(
      new Response('Not found', { status: 404 })
    );

    const req = new Request('http://127.0.0.1/api/reports', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ assetId: assets[0].id }),
    });

    const res = await POST(req);
    const data = await res.json();

    expect(res.status).toBe(201);
    expect(data.report.assetId).toBe(assets[0].id);

    fetchMock.mockRestore();
  });

  it('forwards sections to backend', async () => {
    const fetchMock = vi.spyOn(global, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ report: { id: 1 } }), { status: 201 })
    )
    const req = new Request('http://127.0.0.1/api/reports', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ assetId: assets[0].id, sections: ['summary'] }),
    })
    await POST(req)
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/reports/'),
      expect.objectContaining({
        body: JSON.stringify({ assetId: assets[0].id, sections: ['summary'] }),
      })
    )
    fetchMock.mockRestore()
  })

  it('lists reports', async () => {
    const res = await GET(new Request('http://127.0.0.1/api/reports'));
    const data = await res.json();
    expect(Array.isArray(data.reports)).toBe(true);
  });
});
