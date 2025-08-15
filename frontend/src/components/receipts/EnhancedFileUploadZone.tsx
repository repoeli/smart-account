import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { CloudArrowUpIcon, DocumentIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

interface EnhancedFileUploadZoneProps {
  onFileSelect: (files: File[]) => void;
  maxFiles?: number;
  acceptedTypes?: string[];
  maxSize?: number; // in bytes
  disabled?: boolean;
  showBatchProgress?: boolean;
  currentBatch?: number;
  totalBatches?: number;
}

const EnhancedFileUploadZone: React.FC<EnhancedFileUploadZoneProps> = ({
  onFileSelect,
  maxFiles = 20, // Increased from 10 to 20
  acceptedTypes = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp', 'application/pdf'],
  maxSize = 10 * 1024 * 1024, // 10MB
  disabled = false,
  showBatchProgress = false,
  currentBatch = 0,
  totalBatches = 0,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  const validateFiles = useCallback((files: File[]) => {
    const errors: string[] = [];
    
    if (files.length > maxFiles) {
      errors.push(`Maximum ${maxFiles} files allowed`);
    }
    
    files.forEach((file, index) => {
      if (file.size > maxSize) {
        errors.push(`${file.name} exceeds maximum size of ${formatFileSize(maxSize)}`);
      }
      
      if (!acceptedTypes.includes(file.type)) {
        errors.push(`${file.name} is not a supported file type`);
      }
    });
    
    setValidationErrors(errors);
    return errors.length === 0;
  }, [maxFiles, maxSize, acceptedTypes]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (validateFiles(acceptedFiles)) {
      onFileSelect(acceptedFiles);
      setValidationErrors([]);
    }
  }, [onFileSelect, validateFiles]);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: acceptedTypes.reduce((acc, type) => ({ ...acc, [type]: [] }), {}),
    maxFiles,
    maxSize,
    disabled,
  });

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const acceptedTypesText = acceptedTypes
    .map(type => type.split('/')[1]?.toUpperCase())
    .filter(Boolean)
    .join(', ');

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200
          ${isDragActive && !isDragReject
            ? 'border-primary-500 bg-primary-50'
            : isDragReject
            ? 'border-red-500 bg-red-50'
            : 'border-gray-300 hover:border-gray-400'
          }
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        `}
      >
        <input {...getInputProps()} />
        
        <div className="space-y-4">
          <div className="flex justify-center">
            {isDragActive ? (
              <CloudArrowUpIcon className="h-12 w-12 text-primary-500" />
            ) : (
              <DocumentIcon className="h-12 w-12 text-gray-400" />
            )}
          </div>
          
          <div className="space-y-2">
            <h3 className="text-lg font-medium text-gray-900">
              {isDragActive ? 'Drop your receipts here' : 'Upload Receipts'}
            </h3>
            
            <p className="text-sm text-gray-500">
              {isDragActive
                ? 'Release to upload your receipts'
                : 'Drag and drop your receipt files here, or click to browse'
              }
            </p>
            
            <div className="text-xs text-gray-400 space-y-1">
              <p>Supported formats: {acceptedTypesText}</p>
              <p>Maximum file size: {formatFileSize(maxSize)}</p>
              <p>Maximum files: {maxFiles}</p>
            </div>
          </div>
          
          {!isDragActive && (
            <button
              type="button"
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={disabled}
            >
              Choose Files
            </button>
          )}
        </div>
      </div>

      {/* Batch Progress Indicator */}
      {showBatchProgress && totalBatches > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-blue-900">Batch Upload Progress</span>
            <span className="text-sm text-blue-700">{currentBatch} / {totalBatches}</span>
          </div>
          <div className="w-full bg-blue-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(currentBatch / totalBatches) * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* Validation Errors */}
      {validationErrors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400 mt-0.5 mr-2 flex-shrink-0" />
            <div className="text-sm text-red-700">
              <h4 className="font-medium mb-2">File Validation Errors:</h4>
              <ul className="list-disc list-inside space-y-1">
                {validationErrors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnhancedFileUploadZone;
