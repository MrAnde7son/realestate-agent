/**
 * CRM API client for contacts and leads management
 */

// Analytics tracking
const trackEvent = (eventName: string, properties: Record<string, any>) => {
  // This would integrate with your analytics service
  // For now, just log to console
  console.log('Analytics Event:', eventName, properties);
  
  // Example integration with Google Analytics
  if (typeof window !== 'undefined' && 'gtag' in window) {
    (window as any).gtag('event', eventName, properties);
  }
  
  // Example integration with Mixpanel
  if (typeof window !== 'undefined' && 'mixpanel' in window) {
    (window as any).mixpanel.track(eventName, properties);
  }
};

export interface Contact {
  id: number;
  name: string;
  phone: string;
  email: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface Lead {
  id: number;
  contact: Contact;
  contact_id: number;
  asset_id: number;
  asset_address: string;
  asset_price: number;
  asset_rooms: number;
  asset_area: number;
  status: LeadStatus;
  notes: LeadNote[];
  last_activity_at: string;
  created_at: string;
}

export type LeadStatus = 
  | 'new' 
  | 'contacted' 
  | 'interested' 
  | 'negotiating' 
  | 'closed-won' 
  | 'closed-lost';

export interface LeadNote {
  ts: string;
  text: string;
}

export interface CreateContactData {
  name: string;
  phone?: string;
  email?: string;
  tags?: string[];
}

export interface CreateLeadData {
  contact_id: number;
  asset_id: number;
  status?: LeadStatus;
}

export interface UpdateLeadStatusData {
  status: LeadStatus;
}

export interface AddLeadNoteData {
  text: string;
}

const API_BASE = '/api/crm';

export class CrmApi {
  private static async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const token = localStorage.getItem('access_token');
    
    if (!token) {
      throw new Error('No authentication token found. Please log in to access CRM features.');
    }
    
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers,
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        // Token expired or invalid, redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/auth';
        throw new Error('Authentication expired. Please log in again.');
      }
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Contacts API
  static async getContacts(): Promise<Contact[]> {
    return this.request<Contact[]>('/contacts/');
  }

  static async getContact(id: number): Promise<Contact> {
    return this.request<Contact>(`/contacts/${id}/`);
  }

  static async createContact(data: CreateContactData): Promise<Contact> {
    const contact = await this.request<Contact>('/contacts/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    
    // Track contact creation
    trackEvent('contact_created', {
      contact_id: contact.id,
      has_email: !!contact.email,
      has_phone: !!contact.phone,
      tags_count: contact.tags.length,
      contact_name: contact.name
    });
    
    return contact;
  }

  static async updateContact(id: number, data: Partial<CreateContactData>): Promise<Contact> {
    const contact = await this.request<Contact>(`/contacts/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
    
    // Track contact update
    trackEvent('contact_updated', {
      contact_id: contact.id,
      fields_changed: Object.keys(data),
      contact_name: contact.name
    });
    
    return contact;
  }

  static async deleteContact(id: number): Promise<void> {
    return this.request<void>(`/contacts/${id}/`, {
      method: 'DELETE',
    });
  }

  static async searchContacts(query: string): Promise<Contact[]> {
    const contacts = await this.request<Contact[]>(`/contacts/search/?q=${encodeURIComponent(query)}`);
    
    // Track search event
    trackEvent('crm_search', {
      search_type: 'contacts',
      search_query: query,
      results_count: contacts.length,
      query_length: query.length
    });
    
    return contacts;
  }

  // Leads API
  static async getLeads(): Promise<Lead[]> {
    return this.request<Lead[]>('/leads/');
  }

  static async getLead(id: number): Promise<Lead> {
    return this.request<Lead>(`/leads/${id}/`);
  }

  static async createLead(data: CreateLeadData): Promise<Lead> {
    const lead = await this.request<Lead>('/leads/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    
    // Track lead creation
    trackEvent('lead_created', {
      lead_id: lead.id,
      status: lead.status,
      asset_id: lead.asset_id,
      contact_id: lead.contact.id,
      contact_name: lead.contact.name
    });
    
    return lead;
  }

  static async updateLead(id: number, data: Partial<CreateLeadData>): Promise<Lead> {
    return this.request<Lead>(`/leads/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  static async deleteLead(id: number): Promise<void> {
    return this.request<void>(`/leads/${id}/`, {
      method: 'DELETE',
    });
  }

  static async getLeadsByAsset(assetId: number): Promise<Lead[]> {
    return this.request<Lead[]>(`/leads/by_asset/?asset_id=${assetId}`);
  }

  static async updateLeadStatus(id: number, data: UpdateLeadStatusData): Promise<Lead> {
    const lead = await this.request<Lead>(`/leads/${id}/set_status/`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
    
    // Track status change
    trackEvent('lead_status_changed', {
      lead_id: lead.id,
      to_status: data.status,
      asset_id: lead.asset_id,
      contact_id: lead.contact.id,
      contact_name: lead.contact.name
    });
    
    return lead;
  }

  static async addLeadNote(id: number, data: AddLeadNoteData): Promise<Lead> {
    const lead = await this.request<Lead>(`/leads/${id}/add_note/`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
    
    // Track note addition
    trackEvent('lead_note_added', {
      lead_id: lead.id,
      note_length: data.text.length,
      status: lead.status,
      asset_id: lead.asset_id,
      contact_id: lead.contact.id,
      contact_name: lead.contact.name
    });
    
    return lead;
  }

  static async sendLeadReport(id: number): Promise<{ message: string; contact_email: string }> {
    const result = await this.request<{ message: string; contact_email: string }>(`/leads/${id}/send_report/`, {
      method: 'POST',
    });
    
    // Track report sending
    trackEvent('lead_report_sent', {
      lead_id: id,
      via: result.contact_email ? 'email' : 'link',
      contact_email: result.contact_email
    });
    
    return result;
  }
}
