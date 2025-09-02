export interface Report {
  id: number;
  assetId: number;
  address: string;
  filename: string;
  createdAt: string;
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
  },
];
