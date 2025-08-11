import React from 'react';
import { CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

interface OCRResult {
  merchant_name?: string;
  total_amount?: string;
  date?: string;
  vat_number?: string;
  receipt_number?: string;
  currency?: string;
  confidence_score: number;
}

interface OCRResultsProps {
  receiptId: string;
  extractedData: OCRResult;
  onDataCorrection: (data: Partial<OCRResult>) => void;
  isEditing?: boolean;
}

const OCRResults: React.FC<OCRResultsProps> = ({
  receiptId,
  extractedData,
  onDataCorrection,
  isEditing = false,
}) => {
  const normalizeConfidence = (raw: number | undefined): number => {
    const n = Number(raw);
    if (Number.isNaN(n)) return 0;
    // Support backends returning 0–1 or 0–100
    let v = n > 1 && n <= 100 ? n / 100 : n;
    if (v < 0) v = 0;
    if (v > 1) v = 1;
    return v;
  };

  const normalizedScore = normalizeConfidence(extractedData.confidence_score);

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-50 border-green-200';
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  const getConfidenceIcon = (score: number) => {
    if (score >= 0.8) return <CheckCircleIcon className="w-4 h-4" />;
    return <ExclamationTriangleIcon className="w-4 h-4" />;
  };

  const getConfidenceText = (score: number) => {
    if (score >= 0.8) return 'High Confidence';
    if (score >= 0.6) return 'Medium Confidence';
    return 'Low Confidence';
  };

  const handleFieldChange = (field: keyof OCRResult, value: string) => {
    onDataCorrection({ [field]: value });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">OCR Results</h3>
        <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getConfidenceColor(normalizedScore)}`}>
          {getConfidenceIcon(normalizedScore)}
          <span className="ml-1">{getConfidenceText(normalizedScore)}</span>
          <span className="ml-2">({Math.round(normalizedScore * 100)}%)</span>
        </div>
      </div>

      {/* Extracted Data Fields */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Merchant Name */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            Merchant Name
          </label>
          {isEditing ? (
            <input
              type="text"
              value={extractedData.merchant_name || ''}
              onChange={(e) => handleFieldChange('merchant_name', e.target.value)}
              className="input-field"
              placeholder="Enter merchant name"
            />
          ) : (
            <div className="p-3 bg-gray-50 border border-gray-200 rounded-md">
              {extractedData.merchant_name || 'Not detected'}
            </div>
          )}
        </div>

        {/* Total Amount */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            Total Amount
          </label>
          {isEditing ? (
            <input
              type="text"
              value={extractedData.total_amount || ''}
              onChange={(e) => handleFieldChange('total_amount', e.target.value)}
              className="input-field"
              placeholder="Enter amount"
            />
          ) : (
            <div className="p-3 bg-gray-50 border border-gray-200 rounded-md">
              {extractedData.total_amount ? `${extractedData.currency || '£'}${extractedData.total_amount}` : 'Not detected'}
            </div>
          )}
        </div>

        {/* Date (DD/MM/YYYY) */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            Date
          </label>
          {isEditing ? (
            <input
              type="text"
              inputMode="numeric"
              pattern="\\d{2}/\\d{2}/\\d{4}"
              placeholder="DD/MM/YYYY"
              value={extractedData.date || ''}
              onChange={(e) => handleFieldChange('date', e.target.value)}
              className="input-field"
            />
          ) : (
            <div className="p-3 bg-gray-50 border border-gray-200 rounded-md">
              {extractedData.date || 'Not detected'}
            </div>
          )}
        </div>

        {/* VAT Number */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            VAT Number
          </label>
          {isEditing ? (
            <input
              type="text"
              value={extractedData.vat_number || ''}
              onChange={(e) => handleFieldChange('vat_number', e.target.value)}
              className="input-field"
              placeholder="Enter VAT number"
            />
          ) : (
            <div className="p-3 bg-gray-50 border border-gray-200 rounded-md">
              {extractedData.vat_number || 'Not detected'}
            </div>
          )}
        </div>

        {/* Receipt Number */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            Receipt Number
          </label>
          {isEditing ? (
            <input
              type="text"
              value={extractedData.receipt_number || ''}
              onChange={(e) => handleFieldChange('receipt_number', e.target.value)}
              className="input-field"
              placeholder="Enter receipt number"
            />
          ) : (
            <div className="p-3 bg-gray-50 border border-gray-200 rounded-md">
              {extractedData.receipt_number || 'Not detected'}
            </div>
          )}
        </div>

        {/* Currency */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            Currency
          </label>
          {isEditing ? (
            <select
              value={extractedData.currency || 'GBP'}
              onChange={(e) => handleFieldChange('currency', e.target.value)}
              className="input-field"
            >
              <option value="GBP">GBP (£)</option>
              <option value="EUR">EUR (€)</option>
              <option value="USD">USD ($)</option>
            </select>
          ) : (
            <div className="p-3 bg-gray-50 border border-gray-200 rounded-md">
              {extractedData.currency || 'GBP'}
            </div>
          )}
        </div>
      </div>

      {/* Confidence Score Details */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="text-sm font-medium text-blue-900 mb-2">OCR Confidence</h4>
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-blue-700">Overall Confidence</span>
            <span className="font-medium">{Math.round(normalizedScore * 100)}%</span>
          </div>
          <div className="w-full bg-blue-200 rounded-full h-2 overflow-hidden">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${Math.min(100, Math.max(0, normalizedScore * 100))}%` }}
            />
          </div>
          <p className="text-xs text-blue-600">
            {normalizedScore >= 0.8
              ? 'High confidence - data is likely accurate'
              : normalizedScore >= 0.6
              ? 'Medium confidence - please review the data'
              : 'Low confidence - manual review recommended'
            }
          </p>
        </div>
      </div>
    </div>
  );
};

export default OCRResults; 