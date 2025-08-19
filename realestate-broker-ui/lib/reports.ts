export interface Report {
  id: string;
  listingId: string;
  address: string;
  filename: string;
  createdAt: string;
}

export const reports: Report[] = [
  {
    id: 'r1',
    listingId: 'l1',
    address: 'רחוב הרצל 123, תל אביב',
    filename: 'r1.pdf',
    createdAt: '2024-01-15T08:00:00.000Z',
  },
];
