// API Types for Smart Accounts Management System

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  validation_errors?: Record<string, string[]>;
}

// User Types
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  user_type: 'individual' | 'business';
  status: 'pending_verification' | 'active' | 'suspended' | 'deleted';
  subscription_tier: 'basic' | 'premium' | 'enterprise';
  business_profile?: BusinessProfile;
  phone?: string;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface BusinessProfile {
  company_name: string;
  company_registration: string;
  vat_number?: string;
  address: Address;
  industry?: string;
  company_size?: string;
}

export interface Address {
  street: string;
  city: string;
  state?: string;
  postal_code: string;
  country: string;
}

// Authentication Types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  success: boolean;
  user_id: string;
  email: string;
  first_name: string;
  last_name: string;
  user_type: string;
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

export interface RegisterRequest {
  email: string;
  password: string;
  password_confirm: string;
  first_name: string;
  last_name: string;
  user_type: 'individual' | 'business';
  phone?: string;
  company_name?: string;
  business_type?: string;
  business_profile?: Partial<BusinessProfile>;
}

export interface RegisterResponse {
  success: boolean;
  user_id: string;
  email: string;
  message: string;
  requires_verification: boolean;
}

export interface EmailVerificationRequest {
  email: string;
  verification_token: string;
}

// Receipt Types
export interface Receipt {
  id: string;
  filename: string;
  mime_type?: string;
  status: 'uploaded' | 'processing' | 'processed' | 'failed' | 'archived';
  receipt_type: 'purchase' | 'expense' | 'invoice' | 'bill' | 'other';
  created_at: string;
  updated_at: string;
  file_url: string;
  merchant_name?: string;
  total_amount?: string;
  date?: string;
  category?: string;
  tags?: string[];
  is_business_expense?: boolean;
  confidence_score?: number;
  vat_number?: string;
  receipt_number?: string;
  currency?: string;
  notes?: string;
  // telemetry (optional)
  storage_provider?: 'cloudinary' | 'local' | string;
  cloudinary_public_id?: string;
  // OCR telemetry
  ocr_latency_ms?: number;
  needs_review?: boolean;
}

export interface ReceiptUploadRequest {
  file: File;
  receipt_type: 'purchase' | 'sale' | 'refund' | 'expense';
  ocr_method?: 'paddle_ocr' | 'openai_vision' | 'auto';
}

export interface ReceiptUploadResponse {
  success: boolean;
  receipt_id: string;
  message: string;
  upload_url?: string;
}

export interface ReceiptListResponse {
  success: boolean;
  receipts: Receipt[];
  total_count: number;
  limit: number;
  offset: number;
}

// Cursor search API types
export interface ReceiptSearchItemDTO {
  id: string;
  merchant: string;
  date: string; // YYYY-MM-DD
  amount: number;
  currency: string;
  status: string;
  confidence: number;
  provider: string;
  thumbnailUrl: string;
}

export interface ReceiptSearchPageInfoDTO {
  nextCursor: string | null;
  prevCursor: string | null;
  hasNext: boolean;
  hasPrev: boolean;
}

export interface ReceiptSearchResponseDTO {
  items: ReceiptSearchItemDTO[];
  pageInfo: ReceiptSearchPageInfoDTO;
  totalCount: number | null;
}

export interface ReceiptSearchParams {
  accountId: string;
  q?: string;
  status?: string; // comma-separated
  currency?: string; // comma-separated
  provider?: string; // comma-separated
  dateFrom?: string; // YYYY-MM-DD
  dateTo?: string;   // YYYY-MM-DD
  amountMin?: number;
  amountMax?: number;
  confidenceMin?: number; // 0..1
  sort?: 'date' | 'amount' | 'merchant' | 'confidence';
  order?: 'asc' | 'desc';
  limit?: number; // 12..100
  cursor?: string;
}

// Folder Types
export interface Folder {
  id: string;
  name: string;
  folder_type: 'system' | 'user' | 'smart';
  parent_id?: string;
  description?: string;
  icon?: string;
  color?: string;
  is_favorite: boolean;
  receipt_count: number;
  created_at: string;
  updated_at: string;
}

export interface CreateFolderRequest {
  name: string;
  parent_id?: string;
  description?: string;
  icon?: string;
  color?: string;
}

// Search Types
export interface SearchReceiptsRequest {
  query?: string;
  merchant_names?: string[];
  categories?: string[];
  tags?: string[];
  date_from?: string;
  date_to?: string;
  amount_min?: number;
  amount_max?: number;
  folder_ids?: string[];
  receipt_types?: string[];
  statuses?: string[];
  is_business_expense?: boolean;
  sort_field?: 'date' | 'amount' | 'merchant_name' | 'created_at' | 'updated_at' | 'category';
  sort_direction?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

// Statistics Types
export interface UserStatistics {
  total_receipts: number;
  status_breakdown: Record<string, number>;
  type_breakdown: Record<string, number>;
  monthly_counts: Record<string, number>;
  monthly_amounts: Record<string, string>;
  category_counts: Record<string, number>;
  category_amounts: Record<string, string>;
  total_amount: string;
  business_amount: string;
  personal_amount: string;
  top_merchants: Array<{
    name: string;
    count: number;
    total_amount: string;
  }>;
}

// Bulk Operations
export interface BulkOperationRequest {
  receipt_ids: string[];
  operation: 'add_tags' | 'remove_tags' | 'categorize' | 'mark_business' | 'archive' | 'delete';
  params?: Record<string, any>;
}

// Tags
export interface Tag {
  name: string;
  color?: string;
}

export interface AddTagsRequest {
  tags: string[];
}

// Error Types
export interface ApiError {
  success: false;
  error: string;
  message?: string;
  validation_errors?: Record<string, string[]>;
  status?: number;
}