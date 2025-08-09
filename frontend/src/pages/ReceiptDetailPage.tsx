import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { apiClient } from '../services/api';

const ReceiptDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [receipt, setReceipt] = useState<any>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setIsLoading(true);
        const r = await apiClient.getReceipt(id!);
        setReceipt(r);
      } catch (e: any) {
        setError(e?.message || 'Failed to load receipt');
      } finally {
        setIsLoading(false);
      }
    };
    if (id) load();
  }, [id]);

  if (isLoading) {
    return <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"><div className="card py-8 text-center">Loading…</div></div>;
  }
  if (error || !receipt) {
    return <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"><div className="card py-8 text-center text-red-600">{error || 'Not found'}</div></div>;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Receipt Details</h1>
        <div className="space-x-2">
          <button className="btn-outline" onClick={() => navigate(`/receipts/${id}/ocr`)}>Open OCR Results</button>
          <button className="btn-outline" onClick={() => navigate('/receipts')}>Back to List</button>
        </div>
      </div>
      <div className="card p-6">
        <div className="flex items-start space-x-6">
          <img src={receipt.file_url} alt={receipt.filename} className="h-32 w-32 object-cover rounded bg-gray-100" />
          <div className="flex-1 grid grid-cols-2 gap-4 text-sm">
            <div><span className="text-gray-500">Filename:</span> {receipt.filename}</div>
            <div><span className="text-gray-500">Status:</span> {receipt.status}</div>
            <div><span className="text-gray-500">Merchant:</span> {receipt.merchant_name || '-'}</div>
            <div><span className="text-gray-500">Total:</span> {receipt.currency || 'GBP'} {receipt.total_amount || '-'}</div>
            <div><span className="text-gray-500">Date:</span> {receipt.date ? new Date(receipt.date).toLocaleDateString() : '-'}</div>
            <div><span className="text-gray-500">Confidence:</span> {receipt.confidence_score ? `${Math.round(receipt.confidence_score * 100)}%` : '-'}</div>
            <div><span className="text-gray-500">Storage:</span> {receipt.storage_provider || '-'}</div>
            <div><span className="text-gray-500">Cloudinary ID:</span> {receipt.cloudinary_public_id || '-'}</div>
          </div>
        </div>
      </div>
      <div className="mt-6 card p-6">
        <div className="flex items-center justify-between">
          <div className="font-semibold">Actions</div>
          <div className="space-x-2">
            <button className="btn-outline" onClick={() => apiClient.reprocessReceipt(id!, 'paddle_ocr').then(() => window.location.reload())}>Reprocess (Paddle)</button>
            <button className="btn-outline" onClick={() => apiClient.reprocessReceipt(id!, 'openai_vision').then(() => window.location.reload())}>Reprocess (OpenAI)</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReceiptDetailPage;