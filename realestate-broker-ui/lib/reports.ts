export interface Report {
  id: string;
  listingId: string;
  address: string;
  filename: string;
  createdAt: string;
}

export const reports: Report[] = [
  {
    id: 'r2',
    listingId: 'l2',
    address: 'שדרות רוטשילד 45, תל אביב',
    filename: 'r2.pdf',
    createdAt: '2024-01-20T08:00:00.000Z',
  },
];
