/**
 * Real Estate API TypeScript Client
 * 
 * Auto-generated TypeScript client for the Real Estate API.
 */

export interface APIResponse<T = any> {
  data?: T;
  message?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: {
    id: number;
    email: string;
    username: string;
    role: string;
  };
}

export interface RegisterRequest {
  email: string;
  password: string;
  username: string;
  first_name?: string;
  last_name?: string;
}

export interface Asset {
  id: number;
  address: string;
  street?: string;
  number?: number;
  city?: string;
  normalized_address?: string;
  created_at: string;
  updated_at: string;
}

export interface Permit {
  id: number;
  permit_number: string;
  status: string;
  issue_date?: string;
  expiry_date?: string;
  description?: string;
}

export interface Plan {
  id: number;
  plan_number: string;
  title: string;
  status: string;
  approval_date?: string;
  description?: string;
}

export class APIException extends Error {
  constructor(message: string, public statusCode?: number) {
    super(message);
    this.name = 'APIException';
  }
}

export class AuthenticationError extends APIException {
  constructor(message: string = 'Authentication failed') {
    super(message, 401);
    this.name = 'AuthenticationError';
  }
}

export class ValidationError extends APIException {
  constructor(message: string = 'Validation error') {
    super(message, 400);
    this.name = 'ValidationError';
  }
}

export class NotFoundError extends APIException {
  constructor(message: string = 'Resource not found') {
    super(message, 404);
    this.name = 'NotFoundError';
  }
}

export class ServerError extends APIException {
  constructor(message: string = 'Server error') {
    super(message, 500);
    this.name = 'ServerError';
  }
}

export class RealEstateAPIClient {
  private baseUrl: string;
  private token?: string;

  constructor(baseUrl: string = 'http://localhost:8000/api', token?: string) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.token = token;
  }

  setToken(token: string): void {
    this.token = token;
  }

  private async makeRequest<T = any>(
    method: string,
    endpoint: string,
    data?: any,
    params?: Record<string, string>
  ): Promise<T> {
    const url = new URL(`${this.baseUrl}${endpoint}`);
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        url.searchParams.append(key, value);
      });
    }

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const config: RequestInit = {
      method,
      headers,
    };

    if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
      config.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(url.toString(), config);

      if (response.status === 401) {
        throw new AuthenticationError('Authentication failed. Please check your token.');
      } else if (response.status === 404) {
        throw new NotFoundError(`Resource not found: ${endpoint}`);
      } else if (response.status === 400) {
        const errorText = await response.text();
        throw new ValidationError(`Validation error: ${errorText}`);
      } else if (response.status >= 500) {
        const errorText = await response.text();
        throw new ServerError(`Server error: ${errorText}`);
      } else if (!response.ok) {
        const errorText = await response.text();
        throw new APIException(`API error ${response.status}: ${errorText}`, response.status);
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      } else {
        return { message: await response.text() } as T;
      }
    } catch (error) {
      if (error instanceof APIException) {
        throw error;
      }
      throw new APIException(`Request failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  // Authentication methods
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await this.makeRequest<LoginResponse>('POST', '/auth/login/', credentials);
    
    if (response.access) {
      this.setToken(response.access);
    }
    
    return response;
  }

  async register(userData: RegisterRequest): Promise<APIResponse> {
    return this.makeRequest<APIResponse>('POST', '/auth/register/', userData);
  }

  async refreshToken(refreshToken: string): Promise<LoginResponse> {
    const response = await this.makeRequest<LoginResponse>('POST', '/auth/refresh/', { refresh: refreshToken });
    
    if (response.access) {
      this.setToken(response.access);
    }
    
    return response;
  }

  async logout(): Promise<APIResponse> {
    return this.makeRequest<APIResponse>('POST', '/auth/logout/');
  }

  async getProfile(): Promise<APIResponse> {
    return this.makeRequest<APIResponse>('GET', '/auth/profile/');
  }

  async updateProfile(data: Record<string, any>): Promise<APIResponse> {
    return this.makeRequest<APIResponse>('PUT', '/auth/update-profile/', data);
  }

  // Asset methods
  async getAssets(params?: Record<string, string>): Promise<APIResponse<Asset[]>> {
    return this.makeRequest<APIResponse<Asset[]>>('GET', '/assets/', undefined, params);
  }

  async getAsset(assetId: number): Promise<Asset> {
    return this.makeRequest<Asset>('GET', `/assets/${assetId}/`);
  }

  async createAsset(data: Partial<Asset>): Promise<Asset> {
    return this.makeRequest<Asset>('POST', '/assets/', data);
  }

  async updateAsset(assetId: number, data: Partial<Asset>): Promise<Asset> {
    return this.makeRequest<Asset>('PUT', `/assets/${assetId}/`, data);
  }

  async deleteAsset(assetId: number): Promise<APIResponse> {
    return this.makeRequest<APIResponse>('DELETE', `/assets/${assetId}/`);
  }

  async getAssetStats(): Promise<APIResponse> {
    return this.makeRequest<APIResponse>('GET', '/assets/stats/');
  }

  // Permit methods
  async getPermits(params?: Record<string, string>): Promise<APIResponse<Permit[]>> {
    return this.makeRequest<APIResponse<Permit[]>>('GET', '/permits/', undefined, params);
  }

  async getPermit(permitId: number): Promise<Permit> {
    return this.makeRequest<Permit>('GET', `/permits/${permitId}/`);
  }

  async createPermit(data: Partial<Permit>): Promise<Permit> {
    return this.makeRequest<Permit>('POST', '/permits/', data);
  }

  async updatePermit(permitId: number, data: Partial<Permit>): Promise<Permit> {
    return this.makeRequest<Permit>('PUT', `/permits/${permitId}/`, data);
  }

  async deletePermit(permitId: number): Promise<APIResponse> {
    return this.makeRequest<APIResponse>('DELETE', `/permits/${permitId}/`);
  }

  // Plan methods
  async getPlans(params?: Record<string, string>): Promise<APIResponse<Plan[]>> {
    return this.makeRequest<APIResponse<Plan[]>>('GET', '/plans/', undefined, params);
  }

  async getPlan(planId: number): Promise<Plan> {
    return this.makeRequest<Plan>('GET', `/plans/${planId}/`);
  }

  async createPlan(data: Partial<Plan>): Promise<Plan> {
    return this.makeRequest<Plan>('POST', '/plans/', data);
  }

  async updatePlan(planId: number, data: Partial<Plan>): Promise<Plan> {
    return this.makeRequest<Plan>('PUT', `/plans/${planId}/`, data);
  }

  async deletePlan(planId: number): Promise<APIResponse> {
    return this.makeRequest<APIResponse>('DELETE', `/plans/${planId}/`);
  }

  // Additional methods
  async analyzeMortgage(data: Record<string, any>): Promise<APIResponse> {
    return this.makeRequest<APIResponse>('POST', '/mortgage-analyze/', data);
  }

  async syncAddress(data: Record<string, any>): Promise<APIResponse> {
    return this.makeRequest<APIResponse>('POST', '/sync-address/', data);
  }

  async getTabu(params?: Record<string, string>): Promise<APIResponse> {
    return this.makeRequest<APIResponse>('GET', '/tabu/', undefined, params);
  }

  async getReports(params?: Record<string, string>): Promise<APIResponse> {
    return this.makeRequest<APIResponse>('GET', '/reports/', undefined, params);
  }

  async getAlerts(): Promise<APIResponse> {
    return this.makeRequest<APIResponse>('GET', '/alerts/');
  }

  async createAlert(data: Record<string, any>): Promise<APIResponse> {
    return this.makeRequest<APIResponse>('POST', '/alerts/', data);
  }

  async getAnalyticsTimeseries(params?: Record<string, string>): Promise<APIResponse> {
    return this.makeRequest<APIResponse>('GET', '/analytics/timeseries', undefined, params);
  }
}

export default RealEstateAPIClient;
