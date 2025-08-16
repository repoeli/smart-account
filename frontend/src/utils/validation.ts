import { z } from 'zod';

// Common schemas
const emailSchema = z
  .string()
  .min(1, 'Email is required')
  .email('Please enter a valid email address');

const passwordSchema = z
  .string()
  .min(8, 'Password must be at least 8 characters')
  .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
  .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
  .regex(/[0-9]/, 'Password must contain at least one number')
  .regex(/[^A-Za-z0-9]/, 'Password must contain at least one special character');

const nameSchema = z
  .string()
  .min(1, 'This field is required')
  .min(2, 'Must be at least 2 characters')
  .max(50, 'Must be no more than 50 characters')
  .regex(/^[a-zA-Z\s'-]+$/, 'Only letters, spaces, hyphens and apostrophes allowed');

const phoneSchema = z
  .string()
  .regex(/^(\+44|0)[1-9]\d{8,9}$/, 'Please enter a valid UK phone number')
  .optional()
  .or(z.literal(''));

// Authentication schemas
export const loginSchema = z.object({
  email: emailSchema,
  password: z.string().min(1, 'Password is required'),
});

export const registerSchema = z.object({
  email: emailSchema,
  password: passwordSchema,
  password_confirm: z.string().min(1, 'Please confirm your password'),
  first_name: nameSchema,
  last_name: nameSchema,
  user_type: z.enum(['individual', 'business']).refine(val => val !== undefined, {
    message: 'Please select account type',
  }),
  phone: phoneSchema,
  company_name: z.string().optional(),
  business_type: z.string().optional(),
  terms_accepted: z.boolean().refine(val => val === true, {
    message: 'You must accept the terms and conditions',
  }),
}).refine((data) => data.password === data.password_confirm, {
  message: 'Passwords do not match',
  path: ['password_confirm'],
}).refine((data) => {
  // If user_type is business, require company_name and business_type
  if (data.user_type === 'business') {
    if (!data.company_name || data.company_name.trim() === '') {
      return false;
    }
    if (!data.business_type || data.business_type.trim() === '') {
      return false;
    }
  }
  return true;
}, {
  message: 'Company name and business type are required for business accounts',
  path: ['company_name'],
});

export const businessProfileSchema = z.object({
  company_name: z
    .string()
    .min(1, 'Company name is required')
    .max(100, 'Company name must be no more than 100 characters'),
  company_registration: z
    .string()
    .min(1, 'Company registration number is required')
    .regex(/^[A-Z0-9]{8}$/, 'Must be 8 characters (e.g., 12345678)'),
  vat_number: z
    .string()
    .regex(/^GB\d{9}$/, 'Must be a valid UK VAT number (e.g., GB123456789)')
    .optional()
    .or(z.literal('')),
  industry: z.string().optional(),
  company_size: z.enum(['1-10', '11-50', '51-200', '201-500', '500+']).optional(),
  address: z.object({
    street: z.string().min(1, 'Street address is required'),
    city: z.string().min(1, 'City is required'),
    state: z.string().optional(),
    postal_code: z
      .string()
      .min(1, 'Postal code is required')
      .regex(/^[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}$/i, 'Please enter a valid UK postal code'),
    country: z.string().default('GB'),
  }),
});

export const emailVerificationSchema = z.object({
  email: emailSchema,
  verification_token: z
    .string()
    .min(1, 'Verification code is required')
    .length(6, 'Verification code must be 6 digits')
    .regex(/^\d{6}$/, 'Verification code must contain only numbers'),
});

export const forgotPasswordSchema = z.object({
  email: emailSchema,
});

export const resetPasswordSchema = z.object({
  token: z.string().min(1, 'Reset token is required'),
  password: passwordSchema,
  password_confirm: z.string().min(1, 'Please confirm your password'),
}).refine((data) => data.password === data.password_confirm, {
  message: 'Passwords do not match',
  path: ['password_confirm'],
});

export const profileUpdateSchema = z.object({
  first_name: nameSchema,
  last_name: nameSchema,
  phone: phoneSchema,
  business_profile: businessProfileSchema.optional(),
});

// Type exports
export type LoginFormData = z.infer<typeof loginSchema>;
export type RegisterFormData = z.infer<typeof registerSchema>;
export type BusinessProfileFormData = z.infer<typeof businessProfileSchema>;
export type EmailVerificationFormData = z.infer<typeof emailVerificationSchema>;
export type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>;
export type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;
export type ProfileUpdateFormData = z.infer<typeof profileUpdateSchema>;

export const accountingCompanyRegisterSchema = z.object({
  company_name: z.string().min(1, 'Company name is required'),
  first_name: z.string().min(1, 'First name is required'),
  last_name: z.string().min(1, 'Last name is required'),
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  password_confirm: z.string(),
}).refine((data) => data.password === data.password_confirm, {
  message: "Passwords don't match",
  path: ['password_confirm'],
});

export type AccountingCompanyRegisterFormData = z.infer<typeof accountingCompanyRegisterSchema>;