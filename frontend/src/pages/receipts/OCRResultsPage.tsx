import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { ArrowLeftIcon, PencilIcon, CheckIcon, XMarkIcon } from '@heroicons/react/24/outline';

import OCRResults from '../../components/receipts/OCRResults';
import Button from '../../components/forms/Button';
import { apiClient } from '../../services/api';

interface OCRData {
  merchant_name?: string;
  total_amount?: string;
  date?: string;
  vat_number?: string;
  receipt_number?: string;
  currency?: string;
  confidence_score: number;
}

const OCRResultsPage: React.FC = () => {
  const { receiptId } = useParams<{ receiptId: string }>();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [ocrData, setOcrData] = useState<OCRData>({
    confidence_score: 0,
  });

  useEffect(() => {
    if (receiptId) {
      loadReceiptData();
    }
  }, [receiptId]);

  const loadReceiptData = async () => {
    try {
      setIsLoading(true);
      const receipt = await apiClient.getReceipt(receiptId!);
      
      // Transform receipt data to OCR format
      setOcrData({
        merchant_name: receipt.merchant_name,
        total_amount: receipt.total_amount,
        date: receipt.date,
        vat_number: receipt.vat_number,
        receipt_number: receipt.receipt_number,
        currency: receipt.currency,
        confidence_score: receipt.confidence_score || 0.8,
      });
    } catch (error: any) {
      console.error('Error loading receipt:', error);
      toast.error('Failed to load receipt data');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDataCorrection = (corrections: Partial<OCRData>) => {
    setOcrData(prev => ({ ...prev, ...corrections }));
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      
      await apiClient.updateReceipt(receiptId!, {
        merchant_name: ocrData.merchant_name,
        total_amount: ocrData.total_amount,
        date: ocrData.date,
        vat_number: ocrData.vat_number,
        receipt_number: ocrData.receipt_number,
        currency: ocrData.currency,
      });

      toast.success('Receipt data updated successfully');
      setIsEditing(false);
    } catch (error: any) {
      console.error('Error saving receipt:', error);
      toast.error('Failed to save receipt data');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    // Reload original data
    loadReceiptData();
  };

  const handleReprocess = async () => {
    try {
      setIsLoading(true);
      toast.loading('Reprocessing receipt...');
      
      await apiClient.reprocessReceipt(receiptId!, 'auto');
      
      // Reload the data after reprocessing
      await loadReceiptData();
      
      toast.success('Receipt reprocessed successfully');
    } catch (error: any) {
      console.error('Error reprocessing receipt:', error);
      toast.error('Failed to reprocess receipt');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-4">
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/3"></div>
          </div>
        </div>
      </div>
    );
  }

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
        
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">OCR Results</h1>
            <p className="text-gray-600 mt-2">
              Review and edit the extracted data from your receipt
            </p>
          </div>
          
          <div className="flex items-center space-x-3">
            {!isEditing ? (
              <>
                <Button
                  onClick={() => setIsEditing(true)}
                  variant="outline"
                  className="inline-flex items-center"
                >
                  <PencilIcon className="w-4 h-4 mr-2" />
                  Edit Data
                </Button>
                <Button
                  onClick={handleReprocess}
                  variant="outline"
                  disabled={isLoading}
                >
                  Reprocess
                </Button>
              </>
            ) : (
              <>
                <Button
                  onClick={handleCancel}
                  variant="outline"
                  className="inline-flex items-center"
                >
                  <XMarkIcon className="w-4 h-4 mr-2" />
                  Cancel
                </Button>
                <Button
                  onClick={handleSave}
                  loading={isSaving}
                  className="inline-flex items-center"
                >
                  <CheckIcon className="w-4 h-4 mr-2" />
                  Save Changes
                </Button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* OCR Results */}
      <div className="space-y-6">
        <OCRResults
          receiptId={receiptId!}
          extractedData={ocrData}
          onDataCorrection={handleDataCorrection}
          isEditing={isEditing}
        />

        {/* Action Buttons */}
        {!isEditing && (
          <div className="flex justify-center space-x-4 pt-6 border-t">
            <Button
              onClick={() => navigate(`/receipts/${receiptId}`)}
              variant="outline"
            >
              View Receipt Details
            </Button>
            <Button
              onClick={() => navigate('/receipts')}
            >
              Back to Receipts List
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default OCRResultsPage; 