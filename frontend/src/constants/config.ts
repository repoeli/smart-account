// Application Configuration Constants

export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
} as const;

export const APP_CONFIG = {
  NAME: import.meta.env.VITE_APP_NAME || 'Smart Accounts Management',
  VERSION: import.meta.env.VITE_APP_VERSION || '1.0.0',
  ENVIRONMENT: import.meta.env.VITE_NODE_ENV || 'development',
} as const;

export const UI_CONFIG = {
  THEME: import.meta.env.VITE_THEME || 'light',
  PAGINATION_LIMIT: Number(import.meta.env.VITE_PAGINATION_LIMIT) || 20,
  FILE_UPLOAD_MAX_SIZE: Number(import.meta.env.VITE_FILE_UPLOAD_MAX_SIZE) || 10485760, // 10MB
  DEBOUNCE_DELAY: 300,
  TOAST_DURATION: 5000,
} as const;

export const FEATURES = {
  OCR: import.meta.env.VITE_ENABLE_OCR !== 'false',
  ANALYTICS: import.meta.env.VITE_ENABLE_ANALYTICS !== 'false',
  NOTIFICATIONS: import.meta.env.VITE_ENABLE_NOTIFICATIONS !== 'false',
  DEBUG: import.meta.env.VITE_DEBUG === 'true',
} as const;

export const ROUTES = {
  HOME: '/',
  LOGIN: '/auth/login',
  REGISTER: '/auth/register',
  VERIFY_EMAIL: '/auth/verify-email',
  DASHBOARD: '/dashboard',
  RECEIPTS: '/receipts',
  RECEIPT_DETAIL: '/receipts/:id',
  FOLDERS: '/folders',
  SEARCH: '/search',
  PROFILE: '/profile',
  SETTINGS: '/settings',
} as const;

export const RECEIPT_TYPES = {
  PURCHASE: 'purchase',
  SALE: 'sale',
  REFUND: 'refund',
  EXPENSE: 'expense',
} as const;

export const RECEIPT_STATUSES = {
  UPLOADED: 'uploaded',
  PROCESSING: 'processing',
  PROCESSED: 'processed',
  FAILED: 'failed',
  ARCHIVED: 'archived',
} as const;

export const USER_TYPES = {
  INDIVIDUAL: 'individual',
  BUSINESS: 'business',
} as const;

export const USER_STATUSES = {
  PENDING_VERIFICATION: 'pending_verification',
  ACTIVE: 'active',
  SUSPENDED: 'suspended',
  DELETED: 'deleted',
} as const;

export const SUBSCRIPTION_TIERS = {
  BASIC: 'basic',
  PREMIUM: 'premium',
  ENTERPRISE: 'enterprise',
} as const;

export const OCR_METHODS = {
  PADDLE_OCR: 'paddle_ocr',
  OPENAI_VISION: 'openai_vision',
  AUTO: 'auto',
} as const;

export const SORT_FIELDS = {
  DATE: 'date',
  AMOUNT: 'amount',
  MERCHANT_NAME: 'merchant_name',
  CREATED_AT: 'created_at',
  UPDATED_AT: 'updated_at',
  CATEGORY: 'category',
} as const;

export const SORT_DIRECTIONS = {
  ASC: 'asc',
  DESC: 'desc',
} as const;

export const EXPENSE_CATEGORIES = [
  'accommodation',
  'advertising',
  'automotive',
  'bank_charges',
  'food_and_drink',
  'fuel',
  'insurance',
  'legal_professional',
  'office_supplies',
  'software_subscriptions',
  'telecommunications',
  'travel',
  'other',
] as const;

export const COLORS = {
  PRIMARY: '#3b82f6',
  SECONDARY: '#64748b',
  SUCCESS: '#10b981',
  WARNING: '#f59e0b',
  ERROR: '#ef4444',
  INFO: '#06b6d4',
} as const;

export const BREAKPOINTS = {
  SM: '640px',
  MD: '768px',
  LG: '1024px',
  XL: '1280px',
  '2XL': '1536px',
} as const;