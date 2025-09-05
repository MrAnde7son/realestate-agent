export interface Report {
  id: number;
  assetId: number;
  address: string;
  filename: string;
  createdAt: string;
  /** API URL to download the report PDF */
  url: string;
  status?: string;
}

// Mock data for testing only - not used in production
export const mockReports: Report[] = [
  {
    id: 1,
    assetId: 1,
    address: 'רחוב הרצל 123, תל אביב',
    filename: 'r1.pdf',
    createdAt: '2024-01-15T08:00:00.000Z',
    url: '/api/reports/file/r1.pdf',
  },
];

// Export alias used by tests
export const reports = mockReports;
