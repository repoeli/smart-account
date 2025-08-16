import React, { useEffect, useState, useMemo } from 'react';
import { apiClient } from '../services/api';
import { toast } from 'react-hot-toast';

interface ClientItem { id: string; name: string; email?: string; company_name?: string; phone?: string; address?: string; vat_number?: string; status?: string; }

const ClientsPage: React.FC = () => {
  const [items, setItems] = useState<ClientItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [restrictedMessage, setRestrictedMessage] = useState<string | null>(null);
  const [name, setName] = useState<string>('');
  const [email, setEmail] = useState<string>('');
  const [companyName, setCompanyName] = useState<string>('');
  const [phone, setPhone] = useState<string>('');
  const [address, setAddress] = useState<string>('');
  const [vatNumber, setVatNumber] = useState<string>('');
  const [status, setStatus] = useState<string>('active');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [edit, setEdit] = useState<{ name?: string; email?: string; company_name?: string; phone?: string; address?: string; vat_number?: string; status?: string; }>({});
  const [searchQuery, setSearchQuery] = useState<string>('');

  const filteredItems = useMemo(() => {
    if (!searchQuery) {
      return items;
    }
    return items.filter(client =>
      client.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (client.email && client.email.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (client.company_name && client.company_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (client.phone && client.phone.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (client.vat_number && client.vat_number.toLowerCase().includes(searchQuery.toLowerCase()))
    );
  }, [items, searchQuery]);

  const load = async () => {
    try {
      setLoading(true);
      const res = await apiClient.getClients();
      if (!res?.success) throw new Error('Failed to load');
      setItems(res.items || []);
    } catch (e: any) {
      const status = e?.response?.status;
      const err = e?.response?.data;
      if (status === 403 && err?.error === 'plan_restricted') {
        setRestrictedMessage(err?.message || 'Clients are available on Premium and above.');
        setItems([]);
        setError(null);
      } else {
        setError(e?.message || 'Failed to load clients');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const submit = async () => {
    try {
      if (!name.trim()) { toast.error('Name is required'); return; }
      const res = await apiClient.createClient({
        name: name.trim(),
        email: email || undefined,
        company_name: companyName || undefined,
        phone: phone || undefined,
        address: address || undefined,
        vat_number: vatNumber || undefined,
        status: status || undefined,
      });
      if (!res?.success) throw new Error(res?.message || 'Failed');
      toast.success('Client created');
      setName(''); setEmail(''); setCompanyName(''); setPhone(''); setAddress(''); setVatNumber(''); setStatus('active');
      load();
    } catch (e: any) {
      const status = e?.response?.status;
      const err = e?.response?.data;
      if (status === 403 && err?.error === 'plan_restricted') {
        setRestrictedMessage(err?.message || 'Clients are available on Premium and above.');
        toast.error('Upgrade required to use Clients.');
      } else {
        toast.error(e?.message || 'Failed to create client');
      }
    }
  };

  if (loading) return <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8"><div className="card py-8 text-center">Loading…</div></div>;
  if (error) return <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8"><div className="card py-8 text-center text-red-600">{error}</div></div>;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-bold mb-4">Clients</h1>
      {restrictedMessage && (
        <div className="card p-4 mb-4 border border-yellow-200 bg-yellow-50">
          <div className="flex items-center justify-between">
            <div className="text-sm text-yellow-800">{restrictedMessage}</div>
            <a href="/subscription" className="btn btn-sm btn-primary">Upgrade</a>
          </div>
        </div>
      )}
      <div className="card p-4 mb-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className="block text-xs text-gray-600 mb-1">Name</label>
            <input className="input input-bordered w-full" value={name} onChange={(e)=>setName(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">Email</label>
            <input className="input input-bordered w-full" value={email} onChange={(e)=>setEmail(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">Company Name</label>
            <input className="input input-bordered w-full" value={companyName} onChange={(e)=>setCompanyName(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">Phone</label>
            <input className="input input-bordered w-full" value={phone} onChange={(e)=>setPhone(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">Address</label>
            <input className="input input-bordered w-full" value={address} onChange={(e)=>setAddress(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">VAT Number</label>
            <input className="input input-bordered w-full" value={vatNumber} onChange={(e)=>setVatNumber(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">Status</label>
            <select className="select select-bordered w-full" value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="archived">Archived</option>
            </select>
          </div>
        </div>
        <div className="mt-3">
          <button className="btn btn-primary" onClick={submit} disabled={!!restrictedMessage}>Create</button>
        </div>
      </div>
      <div className="card p-4">
        <div className="mb-4">
          <input
            type="text"
            placeholder="Search clients..."
            className="input input-bordered w-full"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        {filteredItems.length === 0 ? (
          <div className="text-gray-500 text-center">No clients yet.</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left border-b">
                <th className="py-2">Name</th>
                <th className="py-2">Email</th>
                <th className="py-2">Company</th>
                <th className="py-2">Phone</th>
                <th className="py-2">Status</th>
                <th className="py-2" style={{width:120}}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.map(c => (
                <tr key={c.id} className="border-b last:border-0">
                  <td className="py-2">
                    {editingId === c.id ? (
                      <input className="input input-bordered w-full" value={edit.name ?? c.name} onChange={(e)=>setEdit(prev=>({...prev, name:e.target.value}))} />
                    ) : c.name}
                  </td>
                  <td className="py-2">
                    {editingId === c.id ? (
                      <input className="input input-bordered w-full" value={edit.email ?? c.email ?? ''} onChange={(e)=>setEdit(prev=>({...prev, email:e.target.value}))} />
                    ) : (c.email || '-')}
                  </td>
                  <td className="py-2">
                    {editingId === c.id ? (
                      <input className="input input-bordered w-full" value={edit.company_name ?? c.company_name ?? ''} onChange={(e)=>setEdit(prev=>({...prev, company_name:e.target.value}))} />
                    ) : (c.company_name || '-')}
                  </td>
                  <td className="py-2">
                    {editingId === c.id ? (
                      <input className="input input-bordered w-full" value={edit.phone ?? c.phone ?? ''} onChange={(e)=>setEdit(prev=>({...prev, phone:e.target.value}))} />
                    ) : (c.phone || '-')}
                  </td>
                  <td className="py-2">
                    {editingId === c.id ? (
                      <select className="select select-bordered w-full" value={edit.status ?? c.status ?? 'active'} onChange={(e)=>setEdit(prev=>({...prev, status:e.target.value}))}>
                        <option value="active">Active</option>
                        <option value="inactive">Inactive</option>
                        <option value="archived">Archived</option>
                      </select>
                    ) : (c.status || '-')}
                  </td>
                  <td className="py-2">
                    {editingId === c.id ? (
                      <div className="flex gap-2">
                        <button className="btn btn-sm btn-primary" onClick={async()=>{
                          try{
                            const payload:any = {};
                            if (edit.name !== undefined) payload.name = edit.name;
                            if (edit.email !== undefined) payload.email = edit.email;
                            if (edit.company_name !== undefined) payload.company_name = edit.company_name;
                            if (edit.phone !== undefined) payload.phone = edit.phone;
                            if (edit.address !== undefined) payload.address = edit.address;
                            if (edit.vat_number !== undefined) payload.vat_number = edit.vat_number;
                            if (edit.status !== undefined) payload.status = edit.status;
                            const res = await apiClient.updateClient(c.id, payload);
                            if(!res?.success) throw new Error(res?.message || 'Failed');
                            toast.success('Client updated');
                            setEditingId(null); setEdit({});
                            load();
                          }catch(e:any){ toast.error(e?.message || 'Update failed'); }
                        }}>Save</button>
                        <button className="btn btn-sm" onClick={()=>{ setEditingId(null); setEdit({}); }}>Cancel</button>
                      </div>
                    ) : (
                      <div className="flex gap-2">
                        <button className="btn btn-sm" onClick={()=>{ setEditingId(c.id); setEdit({ name:c.name, email:c.email, company_name:c.company_name, phone:c.phone, address:c.address, vat_number:c.vat_number, status:c.status }); }}>Edit</button>
                        <button className="btn btn-sm btn-error" onClick={async()=>{
                          if(!confirm('Delete this client?')) return;
                          try{
                            const res = await apiClient.deleteClient(c.id);
                            if(!res?.success) throw new Error(res?.message || 'Failed');
                            toast.success('Client deleted');
                            load();
                          }catch(e:any){ toast.error(e?.message || 'Delete failed'); }
                        }}>Delete</button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default ClientsPage;


