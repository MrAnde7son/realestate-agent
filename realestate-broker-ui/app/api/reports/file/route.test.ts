import { GET } from './[filename]/route';
import { describe, it, expect, vi, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';

vi.mock('fs', () => ({
  default: {
    readFileSync: vi.fn(),
  }
}));

vi.mock('path', () => ({
  default: {
    join: vi.fn((...args: string[]) => args.join('/')),
  }
}));

describe('reports file API', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('proxies report file from backend', async () => {
    const fetchMock = vi.spyOn(global, 'fetch').mockResolvedValueOnce(
      new Response('pdfdata', { status: 200, headers: { 'Content-Type': 'application/pdf' } })
    );

    const res = await GET(new Request('http://test'), { params: { filename: 'r1.pdf' } });

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/reports/file/r1.pdf'),
      expect.any(Object)
    );
    expect(res.status).toBe(200);
    const buf = await res.arrayBuffer();
    expect(buf.byteLength).toBeGreaterThan(0);
    fetchMock.mockRestore();
  });

  it('falls back to local file when backend fails', async () => {
    const fetchMock = vi.spyOn(global, 'fetch').mockRejectedValueOnce(new Error('fail'));
    vi.mocked(fs.readFileSync).mockReturnValue(Buffer.from('local'));

    const res = await GET(new Request('http://test'), { params: { filename: 'r1.pdf' } });
    expect(fetchMock).toHaveBeenCalled();
    expect(res.status).toBe(200);
    fetchMock.mockRestore();
  });

  it('returns 404 when file not found', async () => {
    vi.spyOn(global, 'fetch').mockRejectedValueOnce(new Error('fail'));
    vi.mocked(fs.readFileSync).mockImplementation(() => { throw new Error('missing'); });

    const res = await GET(new Request('http://test'), { params: { filename: 'missing.pdf' } });
    expect(res.status).toBe(404);
  });
});
