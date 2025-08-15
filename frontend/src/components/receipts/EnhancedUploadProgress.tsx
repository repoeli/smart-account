import React from 'react';
import { CheckCircleIcon, ExclamationCircleIcon, ClockIcon } from '@heroicons/react/24/outline';

interface EnhancedUploadProgressProps {
  progress: number;
  status: 'idle' | 'uploading' | 'processing' | 'completed' | 'error';
  message: string;
  totalFiles: number;
  completedFiles: number;
  failedFiles: number;
  currentFile?: string;
  showDetailedProgress?: boolean;
}

const EnhancedUploadProgress: React.FC<EnhancedUploadProgressProps> = ({
  progress,
  status,
  message,
  totalFiles,
  completedFiles,
  failedFiles,
  currentFile,
  showDetailedProgress = true,
}) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-6 w-6 text-green-500" />;
      case 'error':
        return <ExclamationCircleIcon className="h-6 w-6 text-red-500" />;
      case 'processing':
        return <ClockIcon className="h-6 w-6 text-blue-500 animate-spin" />;
      default:
        return <ClockIcon className="h-6 w-6 text-gray-400" />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'completed':
        return 'bg-green-500';
      case 'error':
        return 'bg-red-500';
      case 'processing':
        return 'bg-blue-500';
      default:
        return 'bg-gray-300';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'completed':
        return 'Upload Completed';
      case 'error':
        return 'Upload Failed';
      case 'processing':
        return 'Processing Receipts';
      case 'uploading':
        return 'Uploading Files';
      default:
        return 'Ready to Upload';
    }
  };

  if (totalFiles === 0) return null;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          {getStatusIcon()}
          <div>
            <h3 className="text-lg font-medium text-gray-900">{getStatusText()}</h3>
            <p className="text-sm text-gray-600">{message}</p>
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-gray-900">{completedFiles}</div>
          <div className="text-sm text-gray-500">of {totalFiles} files</div>
        </div>
      </div>

      {/* Main Progress Bar */}
      <div className="mb-4">
        <div className="flex justify-between text-sm text-gray-600 mb-2">
          <span>Overall Progress</span>
          <span>{Math.round(progress)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className={`h-3 rounded-full transition-all duration-300 ${getStatusColor()}`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Detailed Progress */}
      {showDetailedProgress && (
        <div className="space-y-3">
          {/* File Progress Bars */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-green-600">Completed</span>
                <span className="font-medium">{completedFiles}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${(completedFiles / totalFiles) * 100}%` }}
                />
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-3">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-red-600">Failed</span>
                <span className="font-medium">{failedFiles}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-red-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${(failedFiles / totalFiles) * 100}%` }}
                />
              </div>
            </div>
          </div>

          {/* Current File Info */}
          {currentFile && status === 'uploading' && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <div className="flex items-center space-x-2">
                <ClockIcon className="h-4 w-4 text-blue-500 animate-spin" />
                <span className="text-sm font-medium text-blue-900">Currently uploading:</span>
              </div>
              <p className="text-sm text-blue-700 mt-1 truncate">{currentFile}</p>
            </div>
          )}

          {/* Success Rate */}
          {completedFiles > 0 && (
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-gray-700">Success Rate</span>
                <span className="text-lg font-bold text-gray-900">
                  {Math.round((completedFiles / totalFiles) * 100)}%
                </span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Status Messages */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Status:</span>
          <span className={`font-medium ${
            status === 'completed' ? 'text-green-600' :
            status === 'error' ? 'text-red-600' :
            status === 'processing' ? 'text-blue-600' :
            'text-gray-600'
          }`}>
            {status.charAt(0).toUpperCase() + status.slice(1)}
          </span>
        </div>
      </div>
    </div>
  );
};

export default EnhancedUploadProgress;
