import { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { EnvelopeIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

import { useAppDispatch, useAppSelector } from '../../store';
import { verifyEmail, clearError } from '../../store/slices/authSlice';
import { emailVerificationSchema } from '../../utils/validation';
import type { EmailVerificationFormData } from '../../utils/validation';
import Input from '../../components/forms/Input';
import Button from '../../components/forms/Button';

const EmailVerificationPage = () => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  
  const { isLoading, error } = useAppSelector((state) => state.auth);
  const [isVerified, setIsVerified] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);

  // Get email from location state (passed from registration)
  const emailFromState = (location.state as any)?.email || '';

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<EmailVerificationFormData>({
    resolver: zodResolver(emailVerificationSchema),
    defaultValues: {
      email: emailFromState,
    },
  });

  useEffect(() => {
    if (emailFromState) {
      setValue('email', emailFromState);
    }
  }, [emailFromState, setValue]);

  const onSubmit = async (data: EmailVerificationFormData) => {
    try {
      dispatch(clearError());
      const result = await dispatch(verifyEmail(data));
      
      if (verifyEmail.fulfilled.match(result)) {
        setIsVerified(true);
        toast.success('Email verified successfully!');
        
        // Redirect to login after a short delay
        setTimeout(() => {
          navigate('/auth/login', { 
            state: { message: 'Email verified! Please sign in to continue.' }
          });
        }, 2000);
      } else {
        toast.error(result.payload as string || 'Verification failed');
      }
    } catch (err) {
      toast.error('An unexpected error occurred');
    }
  };

  const handleResendCode = async () => {
    // In a real app, you'd have a separate API endpoint for resending verification codes
    setResendLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      toast.success('Verification code sent to your email');
    } catch (err) {
      toast.error('Failed to resend verification code');
    } finally {
      setResendLoading(false);
    }
  };

  if (isVerified) {
    return (
      <div className="text-center">
        <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 mb-4">
          <CheckCircleIcon className="h-6 w-6 text-green-600" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Email Verified!</h2>
        <p className="text-gray-600 mb-6">
          Your email has been successfully verified. You will be redirected to the login page shortly.
        </p>
        <Button onClick={() => navigate('/auth/login')}>
          Continue to Login
        </Button>
      </div>
    );
  }

  return (
    <div>
      <div className="text-center">
        <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-primary-100 mb-4">
          <EnvelopeIcon className="h-6 w-6 text-primary-600" />
        </div>
        <h2 className="text-3xl font-bold text-gray-900">Verify your email</h2>
        <p className="mt-2 text-sm text-gray-600">
          We've sent a verification code to your email address. Please enter the 6-digit code below.
        </p>
      </div>

      <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

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

        <div className="space-y-1">
          <label className="form-label" htmlFor="verification_token">
            Verification Code <span className="text-red-500">*</span>
          </label>
          <input
            id="verification_token"
            type="text"
            placeholder="Enter 6-digit code"
            maxLength={6}
            className={`input-field text-center text-lg tracking-widest ${
              errors.verification_token ? 'border-red-300 focus:ring-red-500 focus:border-red-500' : ''
            }`}
            {...register('verification_token')}
          />
          {errors.verification_token && (
            <p className="form-error" role="alert">
              {errors.verification_token.message}
            </p>
          )}
          <p className="text-sm text-gray-500">
            Enter the 6-digit code sent to your email
          </p>
        </div>

        <Button
          type="submit"
          className="w-full"
          loading={isLoading}
          disabled={isLoading}
        >
          {isLoading ? 'Verifying...' : 'Verify Email'}
        </Button>

        <div className="text-center space-y-2">
          <p className="text-sm text-gray-600">
            Didn't receive the code?
          </p>
          <Button
            type="button"
            variant="outline"
            size="sm"
            loading={resendLoading}
            disabled={resendLoading}
            onClick={handleResendCode}
          >
            {resendLoading ? 'Sending...' : 'Resend Code'}
          </Button>
        </div>

        <div className="text-center text-sm">
          <Link
            to="/auth/login"
            className="font-medium text-primary-600 hover:text-primary-500 transition-colors"
          >
            Back to Sign in
          </Link>
        </div>
      </form>
    </div>
  );
};

export default EmailVerificationPage;