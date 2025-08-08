import React, { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { ArrowLeftIcon, CameraIcon, PhotoIcon } from '@heroicons/react/24/outline';

import FileUploadZone from '../../components/receipts/FileUploadZone';
import UploadProgress from '../../components/receipts/UploadProgress';
import ReceiptPreview from '../../components/receipts/ReceiptPreview';
import Button from '../../components/forms/Button';
import { apiClient } from '../../services/api';

interface CameraCaptureProps {
  onCapture: (file: File) => void;
  onClose: () => void;
}

const CameraCapture: React.FC<CameraCaptureProps> = ({ onCapture, onClose }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [isCapturing, setIsCapturing] = useState(false);

  const startCamera = useCallback(async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'environment', // Use back camera on mobile
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        }
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        setStream(mediaStream);
      }
    } catch (error) {
      console.error('Camera access error:', error);
      toast.error('Unable to access camera. Please check permissions.');
      onClose();
    }
  }, [onClose]);

  const stopCamera = useCallback(() => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
  }, [stream]);

  const capturePhoto = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return;

    setIsCapturing(true);
    
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');

    if (context) {
      // Set canvas size to match video
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      
      // Draw video frame to canvas
      context.drawImage(video, 0, 0, canvas.width, canvas.height);
      
      // Convert to blob
      canvas.toBlob((blob) => {
        if (blob) {
          const file = new File([blob], `receipt_${Date.now()}.jpg`, {
            type: 'image/jpeg'
          });
          onCapture(file);
          stopCamera();
          onClose();
        }
        setIsCapturing(false);
      }, 'image/jpeg', 0.9);
    }
  }, [onCapture, stopCamera, onClose]);

  React.useEffect(() => {
    startCamera();
    return () => stopCamera();
  }, [startCamera, stopCamera]);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <div className="text-center mb-4">
          <h3 className="text-lg font-semibold">Capture Receipt</h3>
          <p className="text-sm text-gray-600">Position your receipt in the frame</p>
        </div>
        
        <div className="relative mb-4">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full rounded-lg"
          />
          <canvas
            ref={canvasRef}
            className="hidden"
          />
        </div>
        
        <div className="flex space-x-3">
          <Button
            onClick={capturePhoto}
            disabled={isCapturing}
            className="flex-1"
          >
            {isCapturing ? 'Capturing...' : 'Take Photo'}
          </Button>
          <Button
            onClick={() => {
              stopCamera();
              onClose();
            }}
            variant="secondary"
            className="flex-1"
          >
            Cancel
          </Button>
        </div>
      </div>
    </div>
  );
};

const ReceiptUploadPage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'processing' | 'completed' | 'error'>('idle');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadMessage, setUploadMessage] = useState('');
  const [completedFiles, setCompletedFiles] = useState(0);
  const [showCamera, setShowCamera] = useState(false);
  const [isCheckingConnection, setIsCheckingConnection] = useState(false);

  const handleFileSelect = (files: File[]) => {
    setSelectedFiles(prev => [...prev, ...files]);
  };

  const handleRemoveFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleClearAll = () => {
    setSelectedFiles([]);
  };

  const handleCameraCapture = (file: File) => {
    setSelectedFiles(prev => [...prev, file]);
    toast.success('Photo captured successfully!');
  };

  const checkBackendConnection = async () => {
    setIsCheckingConnection(true);
    try {
      await apiClient.healthCheck();
      return true;
    } catch (error) {
      console.error('Backend connection failed:', error);
      toast.error('Cannot connect to backend. Please check if the server is running.');
      return false;
    } finally {
      setIsCheckingConnection(false);
    }
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      toast.error('Please select files to upload');
      return;
    }

    // Check backend connection first
    const isConnected = await checkBackendConnection();
    if (!isConnected) {
      return;
    }

    setUploadStatus('uploading');
    setUploadProgress(0);
    setCompletedFiles(0);
    setUploadMessage('Starting upload...');

    try {
      const totalFiles = selectedFiles.length;
      let successCount = 0;

      for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        setUploadMessage(`Uploading ${file.name}...`);
        
        try {
          const response = await apiClient.uploadReceipt({
            file,
            receipt_type: 'purchase',
            ocr_method: 'auto'
          });

          if (response.success) {
            successCount++;
            setCompletedFiles(successCount);
            toast.success(`Successfully uploaded ${file.name}`);
          } else {
            toast.error(`Failed to upload ${file.name}: ${response.message}`);
          }
        } catch (error: any) {
          console.error('Upload error:', error);
          const errorMessage = error.response?.data?.message || 
                             error.response?.data?.error || 
                             error.message || 
                             'Unknown error';
          toast.error(`Failed to upload ${file.name}: ${errorMessage}`);
        }

        // Update progress
        const progress = ((i + 1) / totalFiles) * 100;
        setUploadProgress(progress);
      }

      setUploadStatus('processing');
      setUploadMessage('Processing receipts with OCR...');

      // Simulate OCR processing time
      setTimeout(() => {
        setUploadStatus('completed');
        setUploadMessage(`Successfully uploaded ${successCount} of ${totalFiles} files`);
        
        if (successCount > 0) {
          toast.success(`Upload completed! ${successCount} receipts processed.`);
          // Navigate to receipts list after successful upload
          setTimeout(() => {
            navigate('/receipts');
          }, 2000);
        }
      }, 2000);

    } catch (error: any) {
      console.error('Upload error:', error);
      setUploadStatus('error');
      setUploadMessage('Upload failed. Please try again.');
      toast.error('Upload failed. Please try again.');
    }
  };

  const isUploading = uploadStatus === 'uploading' || uploadStatus === 'processing';

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => navigate('/receipts')}
          className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 mb-4"
        >
          <ArrowLeftIcon className="w-4 h-4 mr-1" />
          Back to Receipts
        </button>
        
        <h1 className="text-3xl font-bold text-gray-900">Upload Receipts</h1>
        <p className="text-gray-600 mt-2">
          Upload your receipt images or capture them with your camera
        </p>
      </div>

      <div className="space-y-6">
        {/* Upload Options */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* File Upload Zone */}
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6">
            <FileUploadZone
              onFileSelect={handleFileSelect}
              disabled={isUploading}
              maxFiles={20}
              maxSize={10 * 1024 * 1024} // 10MB
            />
          </div>

          {/* Camera Capture */}
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6">
            <div className="text-center">
              <CameraIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Camera Capture</h3>
              <p className="text-sm text-gray-600 mb-4">
                Take a photo of your receipt using your device's camera
              </p>
              <Button
                onClick={() => setShowCamera(true)}
                disabled={isUploading}
                variant="secondary"
                className="w-full"
              >
                <CameraIcon className="w-5 h-5 mr-2" />
                Open Camera
              </Button>
            </div>
          </div>
        </div>

        {/* File Preview */}
        {selectedFiles.length > 0 && (
          <ReceiptPreview
            files={selectedFiles}
            onRemoveFile={handleRemoveFile}
            onClearAll={handleClearAll}
          />
        )}

        {/* Upload Progress */}
        <UploadProgress
          progress={uploadProgress}
          status={uploadStatus}
          message={uploadMessage}
          totalFiles={selectedFiles.length}
          completedFiles={completedFiles}
        />

        {/* Upload Button */}
        {selectedFiles.length > 0 && uploadStatus === 'idle' && (
          <div className="flex justify-center">
            <Button
              onClick={handleUpload}
              className="px-8 py-3 text-lg"
              disabled={isUploading || isCheckingConnection}
            >
              {isCheckingConnection ? 'Checking Connection...' : 
               `Upload ${selectedFiles.length} Receipt${selectedFiles.length !== 1 ? 's' : ''}`}
            </Button>
          </div>
        )}

        {/* Upload Tips */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="text-sm font-medium text-blue-900 mb-2">Upload Tips</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Supported formats: JPEG, PNG, PDF</li>
            <li>• Maximum file size: 10MB per file</li>
            <li>• Ensure receipts are clearly visible and well-lit</li>
            <li>• Avoid blurry or low-resolution images</li>
            <li>• OCR processing may take a few seconds per receipt</li>
            <li>• Camera capture works best with good lighting</li>
          </ul>
        </div>

        {/* Connection Status */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h3 className="text-sm font-medium text-yellow-900 mb-2">Connection Status</h3>
          <p className="text-sm text-yellow-800">
            If you're having trouble uploading, please ensure the backend server is running.
            You can test the connection by clicking the upload button.
          </p>
        </div>
      </div>

      {/* Camera Capture Modal */}
      {showCamera && (
        <CameraCapture
          onCapture={handleCameraCapture}
          onClose={() => setShowCamera(false)}
        />
      )}
    </div>
  );
};

export default ReceiptUploadPage; 