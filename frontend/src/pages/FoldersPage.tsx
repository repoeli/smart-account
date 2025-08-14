import React from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

const apiBase = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

type Folder = { id: string; name: string; folder_type: string; parent_id?: string | null; receipt_count: number };
type ReceiptLite = { id: string; filename: string; file_url: string; created_at: string; merchant_name?: string; total_amount?: string };

const FoldersPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const currentFolderId = searchParams.get('folder_id') || '';
  const [folders, setFolders] = React.useState<Folder[]>([]);
  const [receipts, setReceipts] = React.useState<ReceiptLite[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [showNewFolder, setShowNewFolder] = React.useState(false);
  const [newFolderName, setNewFolderName] = React.useState('');

  const authHeader = React.useMemo(() => ({ 'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`, 'Content-Type': 'application/json' }), []);

  const load = React.useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const searchUrl = new URL(`${apiBase}/receipts/search/`);
      if (currentFolderId) searchUrl.searchParams.append('folder_ids', currentFolderId);
      searchUrl.searchParams.set('limit', '50');

      const [fRes, rRes] = await Promise.all([
        fetch(`${apiBase}/folders/`, { headers: authHeader }),
        fetch(searchUrl.toString(), { headers: authHeader })
      ]);

      const fText = await fRes.text();
      const rText = await rRes.text();
      let fData: any = {};
      let rData: any = {};
      try { fData = fText ? JSON.parse(fText) : {}; } catch { /* ignore non-JSON */ }
      try { rData = rText ? JSON.parse(rText) : {}; } catch { /* ignore non-JSON */ }

      if (!fRes.ok || !fData?.success) throw new Error(fData?.message || fText || 'Failed to load folders');
      if (!rRes.ok || !rData?.success) throw new Error(rData?.error || rText || 'Failed to load receipts');
      setFolders(fData.folders || []);
      setReceipts(rData.receipts || []);
    } catch (e: any) {
      setError(e?.message || 'Failed to load');
    } finally {
      setLoading(false);
    }
  }, [authHeader, currentFolderId]);

  React.useEffect(() => { load(); }, [load]);

  const createFolder = async () => {
    if (!newFolderName.trim()) return;
    try {
      const res = await fetch(`${apiBase}/folders/create/`, { method: 'POST', headers: authHeader, body: JSON.stringify({ name: newFolderName, parent_id: currentFolderId || null }) });
      const data = await res.json();
      if (!res.ok || !data?.success) throw new Error(data?.error || 'Failed to create folder');
      setShowNewFolder(false); setNewFolderName('');
      load();
    } catch (e) {
      alert((e as any)?.message || 'Failed to create folder');
    }
  };

  const openFolder = (id: string) => {
    setSearchParams(prev => { const p = new URLSearchParams(prev); if (id) p.set('folder_id', id); else p.delete('folder_id'); return p; });
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Folders</h1>
        <div className="flex gap-2">
          <button className="btn btn-primary" onClick={() => setShowNewFolder(true)}>New Folder</button>
        </div>
      </div>

      {showNewFolder && (
        <div className="mb-4 flex items-center gap-2">
          <input className="input input-bordered" placeholder="Folder name" value={newFolderName} onChange={e=>setNewFolderName(e.target.value)} />
          <button className="btn btn-primary" onClick={createFolder}>Create</button>
          <button className="btn" onClick={()=>{setShowNewFolder(false); setNewFolderName('');}}>Cancel</button>
        </div>
      )}

      {error && <div className="mb-4 p-3 border border-red-200 bg-red-50 text-red-700 rounded">{error}</div>}
      {loading ? <div>Loading...</div> : (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-1">
            <div className="card p-3">
              <div className="font-semibold mb-2">Folders</div>
              <ul className="space-y-1">
                {folders.map(f => (
                  <li key={f.id}>
                    <button className={`w-full text-left px-2 py-1 rounded ${currentFolderId===f.id?'bg-primary-100 text-primary-700':'hover:bg-gray-50'}`} onClick={()=>openFolder(f.id)}>
                      {f.name}
                      <span className="text-xs text-gray-500 ml-2">({f.receipt_count})</span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <div className="lg:col-span-3">
            <div className="card p-3">
              <div className="font-semibold mb-2">Receipts</div>
              {receipts.length === 0 ? (
                <div className="text-sm text-gray-500">No receipts in this folder.</div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {receipts.map(r => (
                    <a key={r.id} href={`/receipts/${r.id}`} className="block border rounded p-2 hover:bg-gray-50">
                      <div className="font-medium text-gray-800 truncate">{r.merchant_name || r.filename}</div>
                      <div className="text-xs text-gray-500">{new Date(r.created_at).toLocaleString()}</div>
                    </a>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FoldersPage;


