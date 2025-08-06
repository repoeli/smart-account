import { forwardRef } from 'react';
import type { InputHTMLAttributes } from 'react';
import type { FieldError } from 'react-hook-form';
import clsx from 'clsx';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: FieldError;
  label?: string;
  helperText?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ error, label, helperText, className, ...props }, ref) => {
    return (
      <div className="space-y-1">
        {label && (
          <label className="form-label" htmlFor={props.id}>
            {label}
            {props.required && <span className="text-red-500 ml-1">*</span>}
          </label>
        )}
        
        <input
          ref={ref}
          className={clsx(
            error ? 'input-field-error' : 'input-field',
            className
          )}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={
            error ? `${props.id}-error` : helperText ? `${props.id}-helper` : undefined
          }
          {...props}
        />
        
        {error && (
          <p id={`${props.id}-error`} className="form-error" role="alert">
            {error.message}
          </p>
        )}
        
        {helperText && !error && (
          <p id={`${props.id}-helper`} className="form-helper">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;