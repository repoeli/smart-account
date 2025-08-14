import React from 'react';
import { useSearchParams } from 'react-router-dom';

const apiBase = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

type Folder = { id: string; name: string; folder_type: string; parent_id?: string | null; receipt_count: number };
type ReceiptLite = { id: string; filename: string; file_url: string; created_at: string; merchant_name?: string; total_amount?: string };

const FoldersPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const currentFolderId = searchParams.get('folder_id') || '';
  const [folders, setFolders] = React.useState<Folder[]>([]);
  const [receipts, setReceipts] = React.useState<ReceiptLite[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [showNewFolder, setShowNewFolder] = React.useState(false);
  const [newFolderName, setNewFolderName] = React.useState('');
  const [selectedReceiptIds, setSelectedReceiptIds] = React.useState<Set<string>>(new Set());
  const [destinationFolderId, setDestinationFolderId] = React.useState<string>('');

  const authHeader = React.useMemo(() => ({ 'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`, 'Content-Type': 'application/json' }), []);

  const load = React.useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const searchBody: any = { limit: 50 };
      if (currentFolderId) searchBody.folder_ids = [currentFolderId];

      const searchUrl = new URL(`${apiBase}/receipts/search/`);
      searchUrl.searchParams.set('limit', String(searchBody.limit));
      if (currentFolderId) searchUrl.searchParams.append('folder_ids', currentFolderId);
      searchUrl.searchParams.set('_', String(Date.now()));

      const fRes = await fetch(`${apiBase}/folders/`, { headers: authHeader });
      let rRes = await fetch(searchUrl.toString(), { headers: authHeader });
      if (rRes.status === 405) {
        // Server disallows GET; retry with POST
        rRes = await fetch(`${apiBase}/receipts/search/`, { method: 'POST', headers: authHeader, body: JSON.stringify(searchBody) });
      }

      const fText = await fRes.text();
      let fData: any = {};
      try { fData = fText ? JSON.parse(fText) : {}; } catch {}
      if (!fRes.ok || !fData?.success) throw new Error(fData?.message || fText || 'Failed to load folders');
      setFolders(fData.folders || []);

      // Handle receipts response leniently to avoid blocking UI
      const rText = await rRes.text();
      let rData: any = {};
      try { rData = rText ? JSON.parse(rText) : {}; } catch {}
      if (!rRes.ok || !rData?.success) {
        // Treat as empty results when backend is unavailable or returns 4xx/5xx
        setReceipts([]);
      } else {
        setReceipts(rData.receipts || []);
      }
    } catch (e: any) {
      setError(e?.message || 'Failed to load');
    } finally {
      setLoading(false);
    }
  }, [authHeader, currentFolderId]);

  React.useEffect(() => { load(); }, [load]);

  const toggleReceipt = (id: string) => {
    setSelectedReceiptIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const toggleSelectAll = () => {
    setSelectedReceiptIds(prev => {
      if (prev.size === receipts.length) return new Set();
      return new Set(receipts.map(r => r.id));
    });
  };

  const moveSelected = async () => {
    if (!destinationFolderId || selectedReceiptIds.size === 0) return;
    if (destinationFolderId === currentFolderId) return;
    try {
      const res = await fetch(`${apiBase}/folders/${encodeURIComponent(destinationFolderId)}/receipts/`, {
        method: 'POST',
        headers: authHeader,
        body: JSON.stringify({ receipt_ids: Array.from(selectedReceiptIds) })
      });
      const text = await res.text();
      let data: any = {};
      try { data = text ? JSON.parse(text) : {}; } catch {}
      if (!res.ok || !data?.success) throw new Error(data?.message || data?.error || text || 'Failed to move receipts');
      setSelectedReceiptIds(new Set());
      setDestinationFolderId('');
      await load();
    } catch (e: any) {
      alert(e?.message || 'Failed to move receipts');
    }
  };

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
              <div className="flex flex-wrap items-center gap-2 mb-3">
                <button className="btn btn-sm" onClick={toggleSelectAll} disabled={receipts.length===0}>
                  {selectedReceiptIds.size === receipts.length && receipts.length>0 ? 'Clear selection' : 'Select all'}
                </button>
                <span className="text-sm text-gray-600">Selected: {selectedReceiptIds.size}</span>
                <select className="select select-bordered select-sm" value={destinationFolderId} onChange={e=>setDestinationFolderId(e.target.value)}>
                  <option value="">Choose destination folder</option>
                  {folders
                    .filter(f => f.id !== currentFolderId)
                    .map(f => (
                      <option key={f.id} value={f.id}>{f.name}</option>
                    ))}
                </select>
                <button
                  className="btn btn-primary btn-sm"
                  onClick={moveSelected}
                  disabled={selectedReceiptIds.size===0 || !destinationFolderId || destinationFolderId===currentFolderId}
                >
                  Move selected
                </button>
              </div>
              {receipts.length === 0 ? (
                <div className="text-sm text-gray-500">No receipts in this folder.</div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {receipts.map(r => (
                    <div key={r.id} className={`border rounded p-2 hover:bg-gray-50 ${selectedReceiptIds.has(r.id)?'ring-1 ring-primary-400':''}`}>
                      <div className="flex items-start gap-2">
                        <input
                          type="checkbox"
                          className="checkbox checkbox-sm mt-0.5"
                          checked={selectedReceiptIds.has(r.id)}
                          onChange={() => toggleReceipt(r.id)}
                        />
                        <div className="flex-1 min-w-0">
                          <a href={`/receipts/${r.id}`} className="block">
                            <div className="font-medium text-gray-800 truncate">{r.merchant_name || r.filename}</div>
                            <div className="text-xs text-gray-500">{new Date(r.created_at).toLocaleString()}</div>
                          </a>
                        </div>
                      </div>
                    </div>
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


