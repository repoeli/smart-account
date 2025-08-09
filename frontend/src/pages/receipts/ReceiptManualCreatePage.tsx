import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import Button from '../../components/forms/Button';
import { apiClient } from '../../services/api';

const ReceiptManualCreatePage: React.FC = () => {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    merchant_name: '',
    total_amount: '',
    currency: 'GBP',
    date: '',
    notes: '',
    upload_to_cloudinary: true,
    receipt_type: 'purchase',
  });
  const [file, setFile] = useState<File | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const onChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type, checked } = e.target as any;
    setForm((f) => ({ ...f, [name]: type === 'checkbox' ? checked : value }));
  };

  const onSubmit = async () => {
    try {
      setIsSaving(true);
      const data = new FormData();
      Object.entries(form).forEach(([k, v]) => data.append(k, String(v)));
      if (file) data.append('file', file);
      const resp = await apiClient.createManualReceipt(data);
      if (resp?.success) {
        toast.success('Receipt created');
        navigate(`/receipts/${resp.receipt_id}`);
      } else {
        toast.error(resp?.message || 'Failed to create receipt');
      }
    } catch (e: any) {
      toast.error(e?.response?.data?.message || e.message || 'Failed to create receipt');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">New Receipt (Manual)</h1>
      <div className="card p-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-600 mb-1">Merchant</label>
            <input className="input border border-gray-300" name="merchant_name" value={form.merchant_name} onChange={onChange} />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">Total Amount</label>
            <input className="input border border-gray-300" name="total_amount" value={form.total_amount} onChange={onChange} />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">Currency</label>
            <input className="input border border-gray-300" name="currency" value={form.currency} onChange={onChange} />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">Date</label>
            <input type="date" className="input border border-gray-300" name="date" value={form.date} onChange={onChange} />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm text-gray-600 mb-1">Receipt Image (optional)</label>
            <input type="file" className="block w-full text-sm" accept="image/*,application/pdf" onChange={(e) => setFile(e.target.files?.[0] || null)} />
            <label className="mt-2 inline-flex items-center text-sm text-gray-700">
              <input type="checkbox" className="mr-2" name="upload_to_cloudinary" checked={form.upload_to_cloudinary} onChange={onChange} />
              Upload to Cloudinary
            </label>
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm text-gray-600 mb-1">Notes</label>
            <textarea className="input border border-gray-300" name="notes" value={form.notes} onChange={onChange} />
          </div>
        </div>
        <div className="flex gap-2">
          <Button onClick={onSubmit} disabled={isSaving}>{isSaving ? 'Saving...' : 'Create Receipt'}</Button>
          <Button variant="secondary" onClick={() => navigate('/receipts')}>Cancel</Button>
        </div>
      </div>
    </div>
  );
};

export default ReceiptManualCreatePage;


