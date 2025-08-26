export interface Report {
  id: number;
  assetId: number;
  address: string;
  filename: string;
  createdAt: string;
}

export const reports: Report[] = [
  {
    id: 1,
    assetId: 1,
    address: 'רחוב הרצל 123, תל אביב',
    filename: 'r1.pdf',
    createdAt: '2024-01-15T08:00:00.000Z',
  },
];
