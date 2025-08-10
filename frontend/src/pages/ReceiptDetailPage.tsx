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
            <div><span className="text-gray-500">Total:</span> {receipt.currency || 'GBP'} {receipt.total_amount || '-'}</div>
            <div><span className="text-gray-500">Type:</span> {receipt.mime_type || '-'}</div>
            <div><span className="text-gray-500">Date:</span> {receipt.date ? new Date(receipt.date).toLocaleDateString() : '-'}</div>
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
            <button className="btn-outline" onClick={() => apiClient.reprocessReceipt(id!, 'paddle_ocr').then(() => window.location.reload())}>Reprocess (Paddle)</button>
            <button className="btn-outline" onClick={() => apiClient.reprocessReceipt(id!, 'openai_vision').then(() => window.location.reload())}>Reprocess (OpenAI)</button>
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