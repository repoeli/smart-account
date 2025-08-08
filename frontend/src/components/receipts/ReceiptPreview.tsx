import React from 'react';
import { XMarkIcon, DocumentIcon } from '@heroicons/react/24/outline';

interface ReceiptPreviewProps {
  files: File[];
  onRemoveFile: (index: number) => void;
  onClearAll: () => void;
}

const ReceiptPreview: React.FC<ReceiptPreviewProps> = ({
  files,
  onRemoveFile,
  onClearAll,
}) => {
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) {
      return (
        <img
          src={URL.createObjectURL(file)}
          alt={file.name}
          className="w-12 h-12 object-cover rounded"
        />
      );
    }
    return <DocumentIcon className="w-12 h-12 text-gray-400" />;
  };

  if (files.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">
          Selected Files ({files.length})
        </h3>
        {files.length > 1 && (
          <button
            type="button"
            onClick={onClearAll}
            className="text-sm text-red-600 hover:text-red-800"
          >
            Clear All
          </button>
        )}
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {files.map((file, index) => (
          <div
            key={`${file.name}-${index}`}
            className="relative border border-gray-200 rounded-lg p-3 hover:border-gray-300 transition-colors"
          >
            <button
              type="button"
              onClick={() => onRemoveFile(index)}
              className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600 transition-colors"
            >
              <XMarkIcon className="w-4 h-4" />
            </button>
            
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0">
                {getFileIcon(file)}
              </div>
              
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {file.name}
                </p>
                <p className="text-xs text-gray-500">
                  {formatFileSize(file.size)}
                </p>
                <p className="text-xs text-gray-400 capitalize">
                  {file.type.split('/')[1]}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ReceiptPreview; 