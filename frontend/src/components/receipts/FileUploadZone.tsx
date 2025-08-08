import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { CloudArrowUpIcon, DocumentIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface FileUploadZoneProps {
  onFileSelect: (files: File[]) => void;
  maxFiles?: number;
  acceptedTypes?: string[];
  maxSize?: number; // in bytes
  disabled?: boolean;
}

const FileUploadZone: React.FC<FileUploadZoneProps> = ({
  onFileSelect,
  maxFiles = 10,
  acceptedTypes = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf'],
  maxSize = 10 * 1024 * 1024, // 10MB
  disabled = false,
}) => {
  const [dragActive, setDragActive] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    onFileSelect(acceptedFiles);
  }, [onFileSelect]);

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
      
      {isDragReject && (
        <div className="absolute inset-0 bg-red-50 border-2 border-red-500 rounded-lg flex items-center justify-center">
          <div className="text-center">
            <XMarkIcon className="h-8 w-8 text-red-500 mx-auto mb-2" />
            <p className="text-red-600 font-medium">Invalid file type</p>
            <p className="text-red-500 text-sm">Please upload valid receipt files</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUploadZone; 