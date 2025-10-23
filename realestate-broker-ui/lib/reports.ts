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

