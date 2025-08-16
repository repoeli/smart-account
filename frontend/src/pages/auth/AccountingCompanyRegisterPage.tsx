import React from 'react';
import { Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'react-hot-toast';
import { useAppDispatch, useAppSelector } from '../../store';
import { registerUser } from '../../store/slices/authSlice';
import { accountingCompanyRegisterSchema } from '../../utils/validation';
import type { AccountingCompanyRegisterFormData } from '../../utils/validation';
import Input from '../../components/forms/Input';
import Button from '../../components/forms/Button';

const AccountingCompanyRegisterPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const { isLoading, error } = useAppSelector((state) => state.auth);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<AccountingCompanyRegisterFormData>({
    resolver: zodResolver(accountingCompanyRegisterSchema),
  });

  const onSubmit = async (data: AccountingCompanyRegisterFormData) => {
    try {
      const result = await dispatch(registerUser({ ...data, user_type: 'accounting_company' }));
      if (registerUser.fulfilled.match(result)) {
        toast.success('Registration successful! Please check your email to verify your account.');
        // Redirect to a confirmation page or login
      } else {
        toast.error(result.payload as string || 'Registration failed');
      }
    } catch (err) {
      toast.error('An unexpected error occurred');
    }
  };

  return (
    <div className="max-w-md mx-auto">
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900">Register your Accounting Firm</h2>
        <p className="mt-2 text-sm text-gray-600">
          Already have an account?{' '}
          <Link to="/auth/login" className="font-medium text-primary-600 hover:text-primary-500">
            Sign in
          </Link>
        </p>
      </div>

      <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
        {error && <p className="text-red-500">{error}</p>}
        <Input id="company_name" type="text" label="Company Name" required error={errors.company_name} {...register('company_name')} />
        <Input id="first_name" type="text" label="First Name" required error={errors.first_name} {...register('first_name')} />
        <Input id="last_name" type="text" label="Last Name" required error={errors.last_name} {...register('last_name')} />
        <Input id="email" type="email" label="Email" required error={errors.email} {...register('email')} />
        <Input id="password" type="password" label="Password" required error={errors.password} {...register('password')} />
        <Input id="password_confirm" type="password" label="Confirm Password" required error={errors.password_confirm} {...register('password_confirm')} />
        <Button type="submit" className="w-full" loading={isLoading}>
          Register
        </Button>
      </form>
    </div>
  );
};

export default AccountingCompanyRegisterPage;
