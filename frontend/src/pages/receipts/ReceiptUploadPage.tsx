import React, { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { ArrowLeftIcon, CameraIcon } from '@heroicons/react/24/outline';

import FileUploadZone from '../../components/receipts/FileUploadZone';
import UploadProgress from '../../components/receipts/UploadProgress';
import ReceiptPreview from '../../components/receipts/ReceiptPreview';
import Button from '../../components/forms/Button';
import { apiClient } from '../../services/api';
import { useUserMedia, releaseAllUserMedia } from '../../hooks/useUserMedia';

interface CameraCaptureProps {
  onCapture: (file: File) => void;
  onClose: () => void;
  variant?: 'modal' | 'inline';
}

const CameraCapture: React.FC<CameraCaptureProps> = ({ onCapture, onClose, variant = 'modal' }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [devices, setDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | ''>(
    localStorage.getItem('cameraDeviceId') || ''
  );
  const [hasFrame, setHasFrame] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const constraints: MediaStreamConstraints = {
    video: selectedDeviceId ? { deviceId: { exact: selectedDeviceId } } : { facingMode: { ideal: 'environment' } },
    audio: false,
  };
  const [restartKey, setRestartKey] = useState(0);
  const { stream } = useUserMedia(constraints, restartKey);

  // (legacy) global stream stopper kept for reference; not used with cached hook

  const startCamera = useCallback(async () => {
    try {
      const all = await navigator.mediaDevices.enumerateDevices();
      const videoInputs = all.filter((d) => d.kind === 'videoinput');
      setDevices(videoInputs);
      if (!stream) return;
      const hasVideo = stream.getVideoTracks().length > 0;
      if (!hasVideo) throw new Error('No video track');

      const video = videoRef.current;
      if (video) {
        // Ensure inline playback and autoplay on mobile browsers
        video.setAttribute('playsinline', 'true');
        video.setAttribute('muted', 'true');
        video.muted = true;
        video.autoplay = true;
        video.srcObject = stream;
        // Ensure playback starts after metadata is ready (fixes black frame on some browsers)
        const play = async () => {
          try {
            await video.play();
          } catch (e) {
            // Swallow autoplay errors; user will press Take Photo anyway
          }
        };
        if (video.readyState >= 2) {
          play();
        } else {
          video.onloadedmetadata = () => {
            play();
          };
        }
        // Detect first frame
        const onLoadedData = () => setHasFrame(true);
        const onCanPlay = () => setHasFrame(true);
        video.addEventListener('loadeddata', onLoadedData);
        video.addEventListener('canplay', onCanPlay);
        setTimeout(() => {
          if (video.videoWidth === 0 || video.videoHeight === 0) setHasFrame(false);
        }, 1500);
        // Store cleanup
        (video as any).__smart_cleanup_listeners__ = () => {
          video.removeEventListener('loadeddata', onLoadedData);
          video.removeEventListener('canplay', onCanPlay);
        };
        // Note: we intentionally do not auto-retry to avoid play/pause race conditions
      }
    } catch (error) {
      console.error('Camera access error:', error);
    }
  }, [onClose, selectedDeviceId, stream]);

  const stopCamera = useCallback(() => {
    try {
      if (stream) stream.getTracks().forEach((track) => track.stop());
    } finally {
      if (videoRef.current) {
        const video = videoRef.current;
        const cleanup = (video as any).__smart_cleanup_listeners__;
        if (cleanup) {
          try { cleanup(); } catch {}
          (video as any).__smart_cleanup_listeners__ = undefined;
        }
        video.pause();
        video.srcObject = null;
        video.removeAttribute('src');
        // Force reflow to fully detach on some browsers
        video.load();
      }
      setHasFrame(false);
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
    if (!stream) return;
    startCamera();
    return () => {
      stopCamera();
    };
  }, [stream, startCamera, stopCamera]);

  // Always stop camera on page hide/unload to avoid stuck indicator
  React.useEffect(() => {
    const onHide = () => stopCamera();
    const onBeforeUnload = () => stopCamera();
    const onVisibility = () => { if (document.hidden) stopCamera(); };
    window.addEventListener('pagehide', onHide);
    window.addEventListener('beforeunload', onBeforeUnload);
    document.addEventListener('visibilitychange', onVisibility);
    return () => {
      window.removeEventListener('pagehide', onHide);
      window.removeEventListener('beforeunload', onBeforeUnload);
      document.removeEventListener('visibilitychange', onVisibility);
    };
  }, [stopCamera]);

  const content = (
    <div className={variant === 'modal' ? 'bg-white rounded-lg p-6 max-w-md w-full mx-4' : ''}>
      <div className="text-center mb-3">
        <h3 className="text-lg font-semibold">Capture Receipt</h3>
        <p className="text-sm text-gray-600">Position your receipt in the frame</p>
      </div>
      <div className={`relative mb-3 ${variant === 'inline' ? 'border rounded-lg overflow-hidden bg-black' : ''}`}>
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className={`${variant === 'inline' ? 'w-full h-64 object-contain bg-black' : 'w-full rounded-lg'}`}
        />
        <canvas ref={canvasRef} className="hidden" />
        {!hasFrame && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center text-white text-xs bg-black/40 px-2 py-1 rounded">
              Camera active but no video. Switch device or use System Camera.
            </div>
          </div>
        )}
      </div>
      {variant === 'inline' && devices.length > 1 && (
        <div className="mb-3">
          <label className="block text-xs text-gray-600 mb-1">Camera</label>
          <select
            className="w-full border rounded px-2 py-1 text-sm"
            value={selectedDeviceId}
            onChange={(e) => {
              const id = e.target.value;
              setSelectedDeviceId(id);
              if (id) localStorage.setItem('cameraDeviceId', id); else localStorage.removeItem('cameraDeviceId');
              releaseAllUserMedia();
              setRestartKey((k) => k + 1);
            }}
          >
            <option value="">Auto (rear preferred)</option>
            {devices.map((d) => (
              <option key={d.deviceId} value={d.deviceId}>
                {d.label || `Camera ${d.deviceId.slice(0, 6)}`}
              </option>
            ))}
          </select>
        </div>
      )}
      {/* Diagnostics panel */}
      <details className="mb-3">
        <summary className="text-xs text-gray-600 cursor-pointer">Diagnostics</summary>
        <pre className="text-[10px] bg-gray-50 p-2 rounded border overflow-auto max-h-40">
{JSON.stringify({
  selectedDeviceId,
  devices: devices.map(d => ({ id: d.deviceId, label: d.label })),
  hasFrame,
  streamTracks: stream ? stream.getTracks().map(t => ({ kind: t.kind, readyState: t.readyState })) : [],
}, null, 2)}
        </pre>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => { releaseAllUserMedia(); setRestartKey(k => k + 1); }}>
            Restart Stream
          </Button>
        </div>
      </details>
      {!hasFrame && (
        <div className="mb-3">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            capture="environment"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) {
                onCapture(file);
                stopCamera();
                onClose();
              }
            }}
          />
          <Button variant="secondary" onClick={() => fileInputRef.current?.click()} className="w-full">
            Use System Camera
          </Button>
        </div>
      )}
      <div className="flex space-x-3">
        <Button onClick={capturePhoto} disabled={isCapturing} className="flex-1">
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
          {variant === 'modal' ? 'Cancel' : 'Close Camera'}
        </Button>
      </div>
    </div>
  );

  if (variant === 'modal') {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
        {content}
      </div>
    );
  }
  return content;
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
  const [usage, setUsage] = useState<{ receipts_this_month: number; max_receipts: number } | null>(null);
  const [planError, setPlanError] = useState<string | null>(null);

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
            toast.error(`Failed to upload ${file.name}: ${response.message || 'We may have saved your file; check Receipts and reprocess if needed.'}`);
          }
        } catch (error: any) {
          console.error('Upload error:', error);
          if (error?.response?.status === 403 && (error.response?.data?.error === 'plan_limit_reached')) {
            setPlanError(error.response?.data?.message || 'Monthly upload limit reached.');
          }
          const errorMessage = error.response?.data?.message || 
                             error.response?.data?.error || 
                             error.message || 
                              'Unknown error';
          toast.error(`Failed to upload ${file.name}: ${errorMessage}. If this persists, check Receipts list; a fallback save may have occurred.`);
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

  // Load subscription usage to show monthly cap and disable uploads if exceeded
  React.useEffect(() => {
    (async () => {
      try {
        const res = await apiClient.getSubscriptionUsage();
        if (res?.success && res?.usage) setUsage(res.usage);
      } catch {}
    })();
  }, []);

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
        {usage && (
          <div className="card p-3 border border-gray-200">
            <div className="flex items-center justify-between text-sm">
              <div>Monthly uploads: {usage.receipts_this_month} / {usage.max_receipts < 0 ? '∞' : usage.max_receipts}</div>
              {planError && <a href="/subscription" className="btn btn-xs btn-primary">Upgrade</a>}
            </div>
            <div className="h-2 bg-gray-100 rounded mt-2">
              {(() => {
                const max = usage.max_receipts < 0 ? Math.max(1, usage.receipts_this_month) : usage.max_receipts || 1;
                const pct = Math.min(100, Math.round((usage.receipts_this_month / max) * 100));
                return <div className={`h-2 rounded ${pct < 80 ? 'bg-green-500' : pct < 100 ? 'bg-yellow-500' : 'bg-red-500'}`} style={{ width: `${pct}%` }} />;
              })()}
            </div>
          </div>
        )}
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
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-4">
            {!showCamera ? (
              <div className="text-center">
                <CameraIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Camera Capture</h3>
                <p className="text-sm text-gray-600 mb-4">Take a photo of your receipt using your device's camera</p>
                <Button onClick={() => setShowCamera(true)} disabled={isUploading} variant="secondary" className="w-full">
                  <CameraIcon className="w-5 h-5 mr-2" />
                  Open Camera
                </Button>
              </div>
            ) : (
              <CameraCapture
                variant="inline"
                onCapture={handleCameraCapture}
                onClose={() => setShowCamera(false)}
              />
            )}
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
              disabled={isUploading || isCheckingConnection || (!!usage && usage.max_receipts >= 0 && usage.receipts_this_month >= usage.max_receipts)}
            >
              {isCheckingConnection ? 'Checking Connection...' : (!!usage && usage.max_receipts >= 0 && usage.receipts_this_month >= usage.max_receipts) ? 'Monthly Limit Reached' : `Upload ${selectedFiles.length} Receipt${selectedFiles.length !== 1 ? 's' : ''}`}
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

      {/* Inline camera is rendered inside the card above when showCamera is true */}
    </div>
  );
};

export default ReceiptUploadPage; 