import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { EyeIcon, EyeSlashIcon, BuildingOfficeIcon, UserIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

import { useAppDispatch, useAppSelector } from '../../store';
import { registerUser, clearError } from '../../store/slices/authSlice';
import { registerSchema } from '../../utils/validation';
import type { RegisterFormData } from '../../utils/validation';
import { isAutoVerificationEnabled } from '../../utils/environment';
import Input from '../../components/forms/Input';
import Button from '../../components/forms/Button';

/**
 * RegisterPage Component
 * 
 * Handles user registration with the following behavior:
 * - In DEVELOPMENT: Users are auto-verified and redirected to login
 * - In PRODUCTION: Users are sent to email verification page
 * 
 * This matches the backend AUTO_VERIFY_DEVELOPMENT_USERS setting
 */
const RegisterPage = () => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  
  const { isLoading, error } = useAppSelector((state) => state.auth);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      user_type: 'individual',
      terms_accepted: false,
    },
  });

  const userType = watch('user_type');

  const onSubmit = async (data: RegisterFormData) => {
    try {
      dispatch(clearError());
      
      // Remove terms_accepted from the data before sending to API
      const { terms_accepted, ...apiData } = data;
      
      const result = await dispatch(registerUser(apiData));
      
      if (registerUser.fulfilled.match(result)) {
        const response = result.payload;
        
        // Check if user is auto-verified (development mode)
        if (response.requires_verification === true && isAutoVerificationEnabled()) {
          // In development, users are auto-verified, so skip verification page
          toast.success('Account created successfully! You can now login.');
          navigate('/auth/login');
        } else {
          // In production, show verification page
          toast.success('Account created successfully! Please check your email to verify your account.');
          navigate('/auth/verify-email', { 
            state: { email: data.email } 
          });
        }
      } else {
        toast.error(result.payload as string || 'Registration failed');
      }
    } catch (err) {
      toast.error('An unexpected error occurred');
    }
  };

  return (
    <div>
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900">Create your account</h2>
        <p className="mt-2 text-sm text-gray-600">
          Already have an account?{' '}
          <Link
            to="/auth/login"
            className="font-medium text-primary-600 hover:text-primary-500 transition-colors"
          >
            Sign in
          </Link>
        </p>
      </div>

      <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Account Type Selection */}
        <div className="space-y-3">
          <label className="form-label">Account Type <span className="text-red-500">*</span></label>
          <div className="grid grid-cols-2 gap-3">
            <label className={`relative flex cursor-pointer rounded-lg border p-4 focus:outline-none ${
              userType === 'individual' 
                ? 'border-primary-600 ring-2 ring-primary-600' 
                : 'border-gray-300'
            }`}>
              <input
                type="radio"
                value="individual"
                className="sr-only"
                {...register('user_type')}
              />
              <div className="flex flex-col items-center w-full">
                <UserIcon className="h-8 w-8 text-gray-400 mb-2" />
                <span className="text-sm font-medium text-gray-900">Individual</span>
                <span className="text-xs text-gray-500">Personal receipts</span>
              </div>
            </label>

            <label className={`relative flex cursor-pointer rounded-lg border p-4 focus:outline-none ${
              userType === 'business' 
                ? 'border-primary-600 ring-2 ring-primary-600' 
                : 'border-gray-300'
            }`}>
              <input
                type="radio"
                value="business"
                className="sr-only"
                {...register('user_type')}
              />
              <div className="flex flex-col items-center w-full">
                <BuildingOfficeIcon className="h-8 w-8 text-gray-400 mb-2" />
                <span className="text-sm font-medium text-gray-900">Business</span>
                <span className="text-xs text-gray-500">Company expenses</span>
              </div>
            </label>
          </div>
          {errors.user_type && (
            <p className="form-error" role="alert">
              {errors.user_type.message}
            </p>
          )}
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Input
            id="first_name"
            type="text"
            label="First name"
            placeholder="Enter your first name"
            autoComplete="given-name"
            required
            error={errors.first_name}
            {...register('first_name')}
          />

          <Input
            id="last_name"
            type="text"
            label="Last name"
            placeholder="Enter your last name"
            autoComplete="family-name"
            required
            error={errors.last_name}
            {...register('last_name')}
          />
        </div>

        <Input
          id="email"
          type="email"
          label="Email address"
          placeholder="Enter your email"
          autoComplete="email"
          required
          error={errors.email}
          {...register('email')}
        />

        <Input
          id="phone"
          type="tel"
          label="Phone number (optional)"
          placeholder="Enter your UK phone number"
          autoComplete="tel"
          helperText="Format: +44 or 0 followed by 10 digits"
          error={errors.phone}
          {...register('phone')}
        />

        {/* Business-specific fields - only show when user_type is 'business' */}
        {userType === 'business' && (
          <div className="space-y-4">
            <Input
              id="company_name"
              type="text"
              label="Company Name"
              placeholder="Enter your company name"
              required
              error={errors.company_name}
              {...register('company_name')}
            />
            
            <div className="space-y-2">
              <label className="form-label">
                Business Type <span className="text-red-500">*</span>
              </label>
              <select
                className="input-field"
                {...register('business_type')}
              >
                <option value="">Select business type</option>
                <option value="accounting">Accounting Firm</option>
                <option value="consulting">Consulting</option>
                <option value="legal">Legal Services</option>
                <option value="real_estate">Real Estate</option>
                <option value="healthcare">Healthcare</option>
                <option value="retail">Retail</option>
                <option value="technology">Technology</option>
                <option value="manufacturing">Manufacturing</option>
                <option value="other">Other</option>
              </select>
              {errors.business_type && (
                <p className="form-error" role="alert">
                  {errors.business_type.message}
                </p>
              )}
            </div>
          </div>
        )}

        <div className="space-y-4">
          <div className="space-y-1">
            <label className="form-label" htmlFor="password">
              Password <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Create a strong password"
                autoComplete="new-password"
                className={`input-field pr-10 ${
                  errors.password ? 'border-red-300 focus:ring-red-500 focus:border-red-500' : ''
                }`}
                {...register('password')}
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? (
                  <EyeSlashIcon className="h-5 w-5 text-gray-400" />
                ) : (
                  <EyeIcon className="h-5 w-5 text-gray-400" />
                )}
              </button>
            </div>
            {errors.password && (
              <p className="form-error" role="alert">
                {errors.password.message}
              </p>
            )}
            <p className="text-xs text-gray-500">
              Must contain at least 8 characters with uppercase, lowercase, number, and special character
            </p>
          </div>

          <div className="space-y-1">
            <label className="form-label" htmlFor="password_confirm">
              Confirm Password <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <input
                id="password_confirm"
                type={showConfirmPassword ? 'text' : 'password'}
                placeholder="Confirm your password"
                autoComplete="new-password"
                className={`input-field pr-10 ${
                  errors.password_confirm ? 'border-red-300 focus:ring-red-500 focus:border-red-500' : ''
                }`}
                {...register('password_confirm')}
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              >
                {showConfirmPassword ? (
                  <EyeSlashIcon className="h-5 w-5 text-gray-400" />
                ) : (
                  <EyeIcon className="h-5 w-5 text-gray-400" />
                )}
              </button>
            </div>
            {errors.password_confirm && (
              <p className="form-error" role="alert">
                {errors.password_confirm.message}
              </p>
            )}
          </div>
        </div>

        <div className="flex items-start">
          <div className="flex items-center h-5">
            <input
              id="terms_accepted"
              type="checkbox"
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              {...register('terms_accepted')}
            />
          </div>
          <div className="ml-3 text-sm">
            <label htmlFor="terms_accepted" className="text-gray-700">
              I agree to the{' '}
              <Link
                to="/terms"
                className="text-primary-600 hover:text-primary-500 transition-colors"
                target="_blank"
              >
                Terms of Service
              </Link>{' '}
              and{' '}
              <Link
                to="/privacy"
                className="text-primary-600 hover:text-primary-500 transition-colors"
                target="_blank"
              >
                Privacy Policy
              </Link>
              <span className="text-red-500 ml-1">*</span>
            </label>
            {errors.terms_accepted && (
              <p className="form-error mt-1" role="alert">
                {errors.terms_accepted.message}
              </p>
            )}
          </div>
        </div>

        <Button
          type="submit"
          className="w-full"
          loading={isLoading}
          disabled={isLoading}
        >
          {isLoading ? 'Creating account...' : 'Create account'}
        </Button>

        <div className="text-center text-xs text-gray-500">
          <p>
            By creating an account, you acknowledge that your personal data will be processed 
            in accordance with our Privacy Policy and you consent to receive communications 
            from Smart Accounts Management.
          </p>
        </div>
      </form>
    </div>
  );
};

export default RegisterPage;