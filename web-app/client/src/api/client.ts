import axios from 'axios';
import { ProcessedImage, ImageSearchResponse, StatsResponse, SummaryStats, SearchFilters } from '../types/image';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Add request interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const imageApi = {
  // Get paginated images
  getImages: async (params: {
    page?: number;
    limit?: number;
    sort?: string;
    order?: string;
    status?: string;
  } = {}): Promise<ImageSearchResponse> => {
    const response = await apiClient.get('/images', { params });
    return response.data;
  },

  // Get single image by ID
  getImage: async (id: string): Promise<ProcessedImage> => {
    const response = await apiClient.get(`/images/${id}`);
    return response.data;
  },

  // Update image metadata
  updateImageMetadata: async (id: string, metadata: Partial<ProcessedImage>): Promise<{ message: string }> => {
    const response = await apiClient.put(`/images/${id}/metadata`, metadata);
    return response.data;
  },

  // Advanced search with filters
  searchImages: async (filters: SearchFilters & { page?: number; limit?: number; sort?: string; order?: string }): Promise<ImageSearchResponse> => {
    const response = await apiClient.post('/search', filters);
    return response.data;
  },

  // Get search suggestions
  getSearchSuggestions: async (query: string): Promise<{ suggestions: string[] }> => {
    const response = await apiClient.get('/search/suggestions', { params: { q: query } });
    return response.data;
  },
};

export const statsApi = {
  // Get full statistics
  getStats: async (): Promise<StatsResponse> => {
    const response = await apiClient.get('/stats');
    return response.data;
  },

  // Get summary statistics
  getSummaryStats: async (): Promise<SummaryStats> => {
    const response = await apiClient.get('/stats/summary');
    return response.data;
  },
};

export const healthApi = {
  // Check API health
  checkHealth: async (): Promise<{ status: string; timestamp: string; uptime: number; environment: string }> => {
    const response = await apiClient.get('/health');
    return response.data;
  },
};