import axios from 'axios';
import type { AxiosInstance, AxiosResponse } from 'axios';
import { toast } from 'react-hot-toast';
import type {
  ApiResponse,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  EmailVerificationRequest,
  User,
  Receipt,
  ReceiptUploadRequest,
  ReceiptUploadResponse,
  ReceiptListResponse,
  Folder,
  CreateFolderRequest,
  SearchReceiptsRequest,
  UserStatistics,
  BulkOperationRequest,
  AddTagsRequest,
  ReceiptSearchParams,
  ReceiptSearchResponseDTO
} from '../types/api';

class ApiClient {
  private client: AxiosInstance;
  private baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

  constructor() {
    this.client = axios.create({
      baseURL: this.baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const refreshToken = this.getRefreshToken();
            if (refreshToken) {
              const response = await this.refreshAccessToken(refreshToken);
              this.setTokens(response.data.access, refreshToken);
              originalRequest.headers.Authorization = `Bearer ${response.data.access}`;
              return this.client(originalRequest);
            }
          } catch (refreshError) {
            this.logout();
            window.location.href = '/auth/login';
            return Promise.reject(refreshError);
          }
        }

        // Handle other errors
        if (error.response?.status >= 500) {
          toast.error('Server error. Please try again later.');
        } else if (error.response?.status === 404) {
          toast.error('Resource not found.');
        } else if (error.response?.data?.message) {
          toast.error(error.response.data.message);
        }

        return Promise.reject(error);
      }
    );
  }

  // Token management
  private getToken(): string | null {
    return localStorage.getItem('access_token');
  }

  private getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  }

  private setTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  }

  private removeTokens(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  }

  public logout(): void {
    this.removeTokens();
  }

  // Authentication endpoints
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await this.client.post<LoginResponse>('/auth/login/', credentials);
    if (response.data.access_token && response.data.refresh_token) {
      this.setTokens(response.data.access_token, response.data.refresh_token);
      // User profile will be fetched via getCurrentUser after login
    }
    return response.data;
  }

  async register(userData: RegisterRequest): Promise<RegisterResponse> {
    const response = await this.client.post<RegisterResponse>('/auth/register/', userData);
    return response.data;
  }

  async verifyEmail(data: EmailVerificationRequest): Promise<ApiResponse> {
    const response = await this.client.post<ApiResponse>('/auth/verify-email/', data);
    return response.data;
  }

  async refreshAccessToken(refreshToken: string): Promise<AxiosResponse<{ access: string }>> {
    return this.client.post('/auth/token/refresh/', { refresh: refreshToken });
  }

  // User management
  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>('/users/profile/');
    return response.data;
  }

  async updateProfile(userData: Partial<User>): Promise<User> {
    const response = await this.client.put<User>('/users/profile/', userData);
    return response.data;
  }

  // Receipt endpoints
  async uploadReceipt(data: ReceiptUploadRequest): Promise<ReceiptUploadResponse> {
    const formData = new FormData();
    formData.append('file', data.file);
    formData.append('receipt_type', data.receipt_type);
    if (data.ocr_method) {
      formData.append('ocr_method', data.ocr_method);
    }

    const response = await this.client.post<ReceiptUploadResponse>('/receipts/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async createManualReceipt(payload: FormData | Record<string, any>): Promise<{ success: boolean; receipt_id?: string; file_url?: string; message?: string }>{
    let data: any = payload;
    let config: any = {};
    if (typeof FormData !== 'undefined' && payload instanceof FormData) {
      config.headers = { 'Content-Type': 'multipart/form-data' };
    }
    const response = await this.client.post('/receipts/manual/', data, config);
    return response.data;
  }

  async getReceipts(params?: {
    limit?: number;
    offset?: number;
    folder_id?: string;
  }): Promise<ReceiptListResponse> {
    const response = await this.client.get<ReceiptListResponse>('/receipts/', { params });
    // normalize telemetry for latency and needs_review when present
    const normalized = {
      ...response.data,
      receipts: (response.data.receipts as any[]).map((r: any) => ({
        ...r,
        mime_type: r.mime_type,
        ocr_latency_ms: r.ocr_data?.additional_data?.latency_ms || r.metadata?.custom_fields?.latency_ms,
        needs_review: r.metadata?.custom_fields?.needs_review || r.ocr_data?.additional_data?.needs_review,
      })),
    } as any;
    return normalized;
  }

  async getReceipt(id: string): Promise<Receipt> {
    const response = await this.client.get<{ success: boolean; receipt: any }>(`/receipts/${id}/`);
    const r = response.data.receipt;
    // Normalize file_url to absolute if backend returned a relative path
    const apiBase = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
    const publicBase = apiBase.replace(/\/?api\/v1\/?$/, '');
    const normalizedFileUrl = typeof r.file_url === 'string' && r.file_url.startsWith('/')
      ? `${publicBase}${r.file_url}`
      : r.file_url;
    return {
      id: r.id,
      filename: r.filename,
      mime_type: r.mime_type,
      status: r.status,
      receipt_type: r.receipt_type,
      created_at: r.created_at,
      updated_at: r.updated_at,
      file_url: normalizedFileUrl,
      merchant_name: r.ocr_data?.merchant_name,
      total_amount: r.ocr_data?.total_amount,
      date: r.ocr_data?.date,
      confidence_score: r.ocr_data?.confidence_score,
      currency: r.ocr_data?.currency,
      vat_number: r.ocr_data?.vat_number,
      receipt_number: r.ocr_data?.receipt_number,
      metadata: r.metadata,
      storage_provider: r.metadata?.custom_fields?.storage_provider,
      cloudinary_public_id: r.metadata?.custom_fields?.cloudinary_public_id,
      ocr_latency_ms: r.ocr_data?.additional_data?.latency_ms || r.metadata?.custom_fields?.latency_ms,
      needs_review: r.metadata?.custom_fields?.needs_review || r.ocr_data?.additional_data?.needs_review,
    } as unknown as Receipt;
  }

  async updateReceipt(id: string, data: Partial<Receipt>): Promise<Receipt> {
    const response = await this.client.put<Receipt>(`/receipts/${id}/update/`, data);
    return response.data;
  }

  async reprocessReceipt(id: string, ocrMethod: string): Promise<ApiResponse> {
    const response = await this.client.post<ApiResponse>(`/receipts/${id}/reprocess/`, {
      ocr_method: ocrMethod,
    });
    return response.data;
  }

  async validateReceipt(id: string, data: any): Promise<ApiResponse> {
    const response = await this.client.put<ApiResponse>(`/receipts/${id}/validate/`, data);
    return response.data;
  }

  async categorizeReceipt(id: string): Promise<ApiResponse> {
    const response = await this.client.post<ApiResponse>(`/receipts/${id}/categorize/`);
    return response.data;
  }

  async addTagsToReceipt(id: string, data: AddTagsRequest): Promise<ApiResponse> {
    const response = await this.client.post<ApiResponse>(`/receipts/${id}/tags/`, data);
    return response.data;
  }

  // Search
  async searchReceipts(params: SearchReceiptsRequest): Promise<ReceiptListResponse> {
    const response = await this.client.post<ReceiptListResponse>('/receipts/search/', params);
    return response.data;
  }

  // New cursor search (GET /receipts)
  async searchReceiptsCursor(params: ReceiptSearchParams, signal?: AbortSignal): Promise<ReceiptSearchResponseDTO> {
    const response = await this.client.get<ReceiptSearchResponseDTO>('/receipts/', {
      params,
      signal,
    });
    return response.data;
  }

  // Transactions (Sprint 2.2)
  async createTransaction(payload: {
    description: string;
    amount: number | string;
    currency?: string;
    type: 'income' | 'expense';
    transaction_date: string; // YYYY-MM-DD
    receipt_id?: string;
    category?: string;
  }): Promise<{ success: boolean; transaction_id?: string; message?: string }>{
    const response = await this.client.post('/transactions/', payload);
    return response.data;
  }

  async updateTransactionCategory(txId: string, category: string | null): Promise<{ success: boolean; message?: string }>{
    const response = await this.client.patch(`/transactions/${txId}/`, { category: category || '' });
    return response.data;
  }

  async hasTransactionForReceipt(receiptId: string): Promise<{ exists: boolean; transaction_id?: string }>{
    try {
      const response = await this.client.get('/transactions/', {
        params: {
          receipt_id: receiptId,
          limit: 1,
          offset: 0,
        },
      });
      const data: any = response.data || {};
      const items = Array.isArray(data.items)
        ? data.items
        : Array.isArray(data.data?.items)
          ? data.data.items
          : Array.isArray(data.results)
            ? data.results
            : [];
      if (items.length > 0) {
        const txId = items[0]?.id ? String(items[0].id) : undefined;
        return { exists: true, transaction_id: txId };
      }
      return { exists: false };
    } catch {
      return { exists: false };
    }
  }

  async suggestCategory(params: { receiptId?: string; merchant?: string }): Promise<{ success: boolean; category?: string }>{
    try {
      const response = await this.client.get('/categories/suggest/', { params });
      return response.data;
    } catch (e) {
      // Graceful fallback when endpoint not ready yet
      return { success: true, category: undefined } as any;
    }
  }

  // Folders
  async getFolders(): Promise<{ success: boolean; folders: Folder[]; total_count: number }> {
    const response = await this.client.get('/folders/');
    return response.data;
  }

  async createFolder(data: CreateFolderRequest): Promise<ApiResponse> {
    const response = await this.client.post<ApiResponse>('/folders/create/', data);
    return response.data;
  }

  async updateFolder(id: string, data: { new_parent_id?: string }): Promise<ApiResponse> {
    const response = await this.client.put<ApiResponse>(`/folders/${id}/`, data);
    return response.data;
  }

  async moveReceiptsToFolder(folderId: string, receiptIds: string[]): Promise<ApiResponse> {
    const response = await this.client.post<ApiResponse>(`/folders/${folderId}/receipts/`, {
      receipt_ids: receiptIds,
    });
    return response.data;
  }

  // Bulk operations
  async bulkOperation(data: BulkOperationRequest): Promise<ApiResponse> {
    const response = await this.client.post<ApiResponse>('/receipts/bulk/', data);
    return response.data;
  }

  // Statistics
  async getUserStatistics(): Promise<{ success: boolean; statistics: UserStatistics }> {
    const response = await this.client.get('/users/statistics/');
    return response.data;
  }

  async getReceiptStatistics(): Promise<ApiResponse> {
    const response = await this.client.get<ApiResponse>('/receipts/statistics/');
    return response.data;
  }

  // File upload helper
  async uploadFile(file: File, uploadUrl: string): Promise<void> {
    const formData = new FormData();
    formData.append('file', file);

    await axios.post(uploadUrl, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    const response = await this.client.get<{ status: string }>('/health/');
    return response.data;
  }
}

// Create and export a singleton instance
export const apiClient = new ApiClient();
export default apiClient;