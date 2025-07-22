import { DocumentationRequest, DocumentationResponse } from '../types';

const API_BASE_URL = 'http://localhost:8000';

class ApiService {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.error?.message || 
          errorData.detail || 
          `HTTP ${response.status}: ${response.statusText}`
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('An unexpected error occurred');
    }
  }

  async generateDocumentation(data: DocumentationRequest): Promise<DocumentationResponse> {
    return this.request<DocumentationResponse>('/generate-documentation', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getProviders(): Promise<any> {
    return this.request<any>('/providers');
  }

  async healthCheck(): Promise<any> {
    return this.request<any>('/health');
  }

  async listDocumentation(): Promise<any> {
    return this.request<any>('/documentation/list');
  }

  async getSavedDocumentation(repoName: string): Promise<any> {
    return this.request<any>(`/documentation/${encodeURIComponent(repoName)}`);
  }
}

export const apiService = new ApiService();