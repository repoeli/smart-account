import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { apiClient } from '../services/api';
import { toast } from 'react-hot-toast';

const ReceiptDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [receipt, setReceipt] = useState<any>(null);
  const [isReprocessing, setIsReprocessing] = useState<boolean>(false);
  const [hasTransaction, setHasTransaction] = useState<boolean>(false);
  const [linkedTransactionId, setLinkedTransactionId] = useState<string | null>(null);
  const formatDisplayDate = React.useCallback((value?: string) => {
    if (!value) return '-';
    // Accept DD/MM/YYYY and display as-is; else try ISO/parsable
    if (/^\d{2}\/\d{2}\/\d{4}$/.test(value)) return value;
    if (/^\d{4}-\d{2}-\d{2}/.test(value)) {
      const d = new Date(value);
      if (!isNaN(d.getTime())) return d.toLocaleDateString();
      // Fallback: convert YYYY-MM-DD to DD/MM/YYYY manually
      try {
        const [y, m, d2] = value.slice(0, 10).split('-');
        return `${d2}/${m}/${y}`;
      } catch {
        return value;
      }
    }
    // Unknown format – do not attempt to parse to prevent Invalid Date
    return value;
  }, []);

  const toTransactionDate = (value?: string) => {
    if (!value) return '';
    if (/^\d{4}-\d{2}-\d{2}/.test(value)) return value.slice(0, 10);
    if (/^\d{2}\/\d{2}\/\d{4}$/.test(value)) {
      const [d, m, y] = value.split('/');
      return `${y}-${m}-${d}`;
    }
    return value;
  };

  const canCreateTransaction = React.useMemo(() => {
    if (!receipt) return false;
    const amountNum = Number(receipt.total_amount);
    if (!isFinite(amountNum) || amountNum <= 0) return false;
    const txDate = toTransactionDate(receipt.date);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(txDate)) return false;
    return true;
  }, [receipt]);
  const cloudinaryAssetUrl = React.useMemo(() => {
    const r = receipt;
    if (!r) return null;
    const fileUrl: string | undefined = r.file_url;
    if (fileUrl && /res\.cloudinary\.com\//.test(fileUrl)) {
      // If the query string contains rt=resource_type from backend, normalize to proper path
      try {
        const u = new URL(fileUrl);
        const rt = u.searchParams.get('rt');
        if (rt && !u.pathname.includes(`/${rt}/`)) {
          return fileUrl.replace('/image/', `/${rt}/`).split('?')[0];
        }
      } catch {}
      return fileUrl;
    }
    const publicId: string | undefined = r.cloudinary_public_id;
    if (!publicId) return null;
    const envName = (import.meta as any).env?.VITE_CLOUDINARY_CLOUD_NAME as string | undefined;
    const inferred = fileUrl?.match(/res\.cloudinary\.com\/([^/]+)/)?.[1];
    const cloudName = envName || inferred;
    if (!cloudName) return null;
    let resourceType = 'image';
    if (fileUrl?.includes('/video/')) resourceType = 'video';
    if ((fileUrl || '').includes('.pdf') || r.mime_type === 'application/pdf') resourceType = 'raw';
    return `https://res.cloudinary.com/${cloudName}/${resourceType}/upload/${publicId}`;
  }, [receipt]);

  useEffect(() => {
    const load = async () => {
      try {
        setIsLoading(true);
        const r = await apiClient.getReceipt(id!);
        setReceipt(r);
        // Prefer API-provided has_transaction if available
        if (typeof r?.has_transaction === 'boolean') setHasTransaction(!!r.has_transaction);
        // Fallback check to also get transaction id for link
        try {
          const apiBase = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
          const url = new URL(`${apiBase}/transactions/`);
          url.searchParams.set('limit', '1');
          url.searchParams.set('offset', '0');
          url.searchParams.set('receipt_id', id!);
          const res = await fetch(url.toString(), { headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}` } });
          const data = await res.json();
          if (res.ok && data?.success && Array.isArray(data.items) && data.items.length > 0) {
            setHasTransaction(true);
            setLinkedTransactionId(String(data.items[0].id));
          }
        } catch {}
      } catch (e: any) {
        const msg = e?.response?.data?.message || e?.message || 'Failed to load receipt';
        setError(msg);
        if (e?.response?.status === 400 && /Not authorized/i.test(msg)) {
          toast.error('You are not authorized to view this receipt.');
          navigate('/receipts');
          return;
        }
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
            <div className="flex items-center gap-2">
              <div>
                <span className="text-gray-500">Status:</span>{' '}
                <span className={`px-2 py-0.5 rounded border ${
                  receipt.status === 'failed' ? 'bg-red-50 text-red-700 border-red-200' :
                  receipt.status === 'processed' ? 'bg-green-50 text-green-700 border-green-200' :
                  receipt.status === 'needs_review' ? 'bg-yellow-50 text-yellow-700 border-yellow-200' : 'bg-gray-50 text-gray-600 border-gray-200'
                }`}>{receipt.status}</span>
              </div>
              {receipt.needs_review && (
                <span title="This receipt needs manual review" className="px-2 py-0.5 rounded border bg-yellow-50 text-yellow-700 border-yellow-200">needs review</span>
              )}
            </div>
            <div><span className="text-gray-500">Merchant:</span> {receipt.merchant_name || '-'}</div>
            <div>
              <span className="text-gray-500">Total:</span>{' '}
              {(() => {
                const currency = receipt.currency || 'GBP';
                const amountNum = Number(receipt.total_amount);
                if (!isNaN(amountNum)) {
                  try {
                    const fmt = new Intl.NumberFormat(undefined, { style: 'currency', currency });
                    return fmt.format(amountNum);
                  } catch {
                    return `${currency} ${receipt.total_amount}`;
                  }
                }
                return `${currency} ${receipt.total_amount || '-'}`;
              })()}
            </div>
            <div><span className="text-gray-500">Type:</span> {receipt.mime_type || '-'}</div>
            <div><span className="text-gray-500">Date:</span> {formatDisplayDate(receipt.date)}</div>
            <div><span className="text-gray-500">Confidence:</span> {receipt.confidence_score ? `${Math.round(receipt.confidence_score * 100)}%` : '-'}</div>
            <div><span className="text-gray-500">OCR Latency:</span> {typeof receipt.ocr_latency_ms === 'number' ? `${receipt.ocr_latency_ms} ms` : '-'}</div>
            <div className="flex items-center gap-2">
              <span className="text-gray-500">Storage:</span> {receipt.storage_provider || '-'}
              {receipt.mime_type === 'application/pdf' && (
                <span className="ml-2 px-1.5 py-0.5 rounded bg-gray-100 border border-gray-300 text-gray-700">PDF</span>
              )}
              {receipt.file_url && (
                <button
                  className="btn-xs btn-outline"
                  onClick={() => { navigator.clipboard.writeText(receipt.file_url); toast.success('File URL copied'); }}
                >Copy File URL</button>
              )}
            </div>
            <div>
              <span className="text-gray-500">Cloudinary ID:</span> {receipt.cloudinary_public_id || '-'}
              {receipt.storage_provider === 'cloudinary' && receipt.cloudinary_public_id && cloudinaryAssetUrl && (
                <>
                  {' '}·{' '}
                  <a
                    href={cloudinaryAssetUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="text-blue-600 hover:underline"
                    onClick={(e) => e.stopPropagation()}
                  >
                    View on Cloudinary
                  </a>
                  {' '}·{' '}
                  <button
                    className="btn-xs btn-outline"
                    onClick={() => { navigator.clipboard.writeText(receipt.cloudinary_public_id); toast.success('Cloudinary ID copied'); }}
                  >Copy ID</button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
      <div className="mt-6 card p-6">
        <div className="flex items-center justify-between">
          <div className="font-semibold">Actions</div>
          <div className="space-x-2">
            <button
              className="btn-outline"
              disabled={isReprocessing}
              onClick={async () => {
                try {
                  setIsReprocessing(true);
                  const res = await apiClient.reprocessReceipt(id!, 'paddle_ocr');
                  if (res?.success) {
                    // Refresh details asynchronously
                    const fresh = await apiClient.getReceipt(id!);
                    setReceipt(fresh);
                    toast.success('Reprocessed with Paddle');
                  } else {
                    toast.error(res?.message || 'Reprocess failed');
                  }
                } catch (e: any) {
                  toast.error(e?.message || 'Reprocess failed');
                } finally {
                  setIsReprocessing(false);
                }
              }}
            >{isReprocessing ? 'Reprocessing…' : 'Reprocess (Paddle)'}
            </button>
            <button
              className="btn-outline"
              disabled={isReprocessing}
              onClick={async () => {
                try {
                  setIsReprocessing(true);
                  const res = await apiClient.reprocessReceipt(id!, 'openai_vision');
                  if (res?.success) {
                    const fresh = await apiClient.getReceipt(id!);
                    setReceipt(fresh);
                    toast.success('Reprocessed with OpenAI Vision');
                  } else {
                    toast.error(res?.message || 'Reprocess failed');
                  }
                } catch (e: any) {
                  toast.error(e?.message || 'Reprocess failed');
                } finally {
                  setIsReprocessing(false);
                }
              }}
            >{isReprocessing ? 'Reprocessing…' : 'Reprocess (OpenAI)'}
            </button>
            <button
              className={`btn-primary ${hasTransaction || !canCreateTransaction ? 'opacity-50 cursor-not-allowed' : ''}`}
              disabled={hasTransaction || !canCreateTransaction}
              onClick={async () => {
                if (hasTransaction || !canCreateTransaction) {
                  if (!canCreateTransaction) {
                    toast.error('Amount and date are required. Open OCR Results to fix data.');
                  }
                  return;
                }
                try {
                  const desc = receipt.merchant_name ? `${receipt.merchant_name} receipt` : 'Receipt expense';
                  const payload = {
                    description: desc,
                    amount: Number(receipt.total_amount) || 0,
                    currency: receipt.currency || 'GBP',
                    type: 'expense' as const,
                    transaction_date: toTransactionDate(receipt.date),
                    receipt_id: id!,
                  };
                  const suggestion = await apiClient.suggestCategory({ receiptId: id!, merchant: receipt.merchant_name });
                  if (suggestion?.success && suggestion?.category) (payload as any).category = suggestion.category;
                  const res = await apiClient.createTransaction(payload as any);
                  if (res?.success) {
                    toast.success('Transaction created');
                    navigate('/transactions');
                  } else {
                    toast.error(res?.message || 'Failed to create transaction');
                  }
                } catch (e: any) {
                  toast.error(e?.message || 'Failed to create transaction');
                }
              }}
            >Create Transaction</button>
            {hasTransaction && (
              <span className="ml-2 text-xs text-gray-600" title="This receipt already has a transaction">
                Already converted{linkedTransactionId ? ' · ' : ''}
                {linkedTransactionId ? (
                  <a
                    className="link"
                    href={`/transactions?receipt_id=${encodeURIComponent(id!)}`}
                    onClick={(e) => {
                      e.preventDefault();
                      window.location.href = `/transactions?receipt_id=${encodeURIComponent(id!)}`;
                    }}
                  >
                    View transaction
                  </a>
                ) : null}
              </span>
            )}
            {receipt?.ocr_latency_ms && (
              <span className="text-xs text-gray-500">OCR latency: {receipt.ocr_latency_ms} ms</span>
            )}
            {receipt?.ocr_data?.additional_data?.source_url && (
              <a href={receipt.ocr_data.additional_data.source_url} target="_blank" rel="noreferrer" className="btn-outline">Open Source URL</a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReceiptDetailPage;