import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../services/api';
import type { Receipt } from '../types/api';

const ReceiptsPage = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleUploadClick = () => {
    navigate('/receipts/upload');
  };

  useEffect(() => {
    const load = async () => {
      try {
        setIsLoading(true);
        const resp = await apiClient.getReceipts({ limit: 50, offset: 0 });
        // Backend returns receipts with nested ocr_data; flatten minimally for display
        const mapped: Receipt[] = (resp.receipts as any[]).map((r: any) => ({
          id: r.id,
          filename: r.filename,
          status: r.status,
          receipt_type: r.receipt_type,
          created_at: r.created_at,
          updated_at: r.updated_at,
          file_url: r.file_url,
          merchant_name: r.ocr_data?.merchant_name,
          total_amount: r.ocr_data?.total_amount,
          date: r.ocr_data?.date,
          confidence_score: r.ocr_data?.confidence_score,
          currency: r.ocr_data?.currency,
        }));
        setReceipts(mapped);
      } catch (e: any) {
        setError(e?.message || 'Failed to load receipts');
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Receipts</h1>
        <div className="space-x-3">
          <button className="btn-secondary" onClick={handleUploadClick}>📷 Capture / Upload</button>
          <button className="btn-primary" onClick={handleUploadClick}>📤 Upload Receipt</button>
        </div>
      </div>
      {isLoading ? (
        <div className="card py-8 text-center text-gray-500">Loading receipts…</div>
      ) : error ? (
        <div className="card py-8 text-center text-red-600">{error}</div>
      ) : receipts.length === 0 ? (
        <div className="card text-center py-12">
          <div className="h-16 w-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-gray-400 text-2xl">📄</span>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No receipts yet</h3>
          <p className="text-gray-500 mb-6">
            Upload your first receipt to get started with smart organization and OCR processing.
          </p>
          <button 
            className="btn-primary"
            onClick={handleUploadClick}
          >
            📤 Upload Your First Receipt
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {receipts.map((r) => (
            <div key={r.id} className="card p-4 cursor-pointer hover:shadow" onClick={() => navigate(`/receipts/${r.id}`)}>
              <div className="flex items-center space-x-4">
                <img
                  src={r.file_url}
                  alt={r.filename}
                  className="h-16 w-16 object-cover rounded bg-gray-100"
                  onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                />
                <div className="flex-1">
                  <div className="font-semibold truncate">{r.merchant_name || r.filename}</div>
                  <div className="text-sm text-gray-500">{r.date ? new Date(r.date).toLocaleDateString() : ''}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-600">{r.currency || 'GBP'} {r.total_amount || ''}</div>
                  <div className={`text-xs ${r.status === 'failed' ? 'text-red-600' : 'text-gray-400'}`}>{r.status}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ReceiptsPage;