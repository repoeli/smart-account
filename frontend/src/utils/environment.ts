/**
 * Environment utilities for detecting development vs production
 */

export const isDevelopment = () => {
  return import.meta.env.DEV || import.meta.env.MODE === 'development';
};

export const isProduction = () => {
  return import.meta.env.PROD || import.meta.env.MODE === 'production';
};

/**
 * Check if auto-verification is enabled (development mode)
 * In development, users are automatically verified and can login immediately
 */
export const isAutoVerificationEnabled = () => {
  return isDevelopment();
}; 