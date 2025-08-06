import type { ReactNode } from 'react';
import type { FieldError } from 'react-hook-form';

interface FormFieldProps {
  label: string;
  error?: FieldError;
  required?: boolean;
  children: ReactNode;
  className?: string;
}

const FormField = ({ label, error, required, children, className = '' }: FormFieldProps) => {
  return (
    <div className={`space-y-1 ${className}`}>
      <label className="form-label">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      {children}
      {error && (
        <p className="form-error" role="alert">
          {error.message}
        </p>
      )}
    </div>
  );
};

export default FormField;