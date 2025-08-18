export interface Report {
  id: string;
  listingId: string;
  address: string;
  filename: string;
  createdAt: string;
}

export const reports: Report[] = [];
