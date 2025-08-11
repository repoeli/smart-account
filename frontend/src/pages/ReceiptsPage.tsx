import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { apiClient } from '../services/api';
import type { ReceiptSearchResponseDTO } from '../types/api';
import type { Receipt } from '../types/api';

const ReceiptsPage = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [convertedMap, setConvertedMap] = useState<Record<string, { exists: boolean; txId?: string }>>({});
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState<string>('');
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const abortRef = useRef<AbortController | null>(null);
  const lastActionRef = useRef<null | (() => void | Promise<void>)>(null);
  const locale = useMemo(() => navigator.language || 'en-GB', []);
  const formatCurrency = useMemo(
    () => (amount?: string | number, currency?: string) => {
      if (amount === undefined || amount === null || amount === '') return '';
      const num = typeof amount === 'number' ? amount : parseFloat(amount);
      if (Number.isNaN(num)) return '';
      try {
        return new Intl.NumberFormat(locale, { style: 'currency', currency: (currency || 'GBP') as any, currencyDisplay: 'narrowSymbol' }).format(num);
      } catch {
        return new Intl.NumberFormat(locale, { style: 'currency', currency: 'GBP' as any }).format(num);
      }
    },
    [locale]
  );
  const formatDate = useMemo(
    () => (iso?: string) => {
      if (!iso) return '';
      const d = new Date(iso);
      if (Number.isNaN(d.getTime())) return iso;
      return new Intl.DateTimeFormat(locale, { year: 'numeric', month: 'short', day: '2-digit' }).format(d);
    },
    [locale]
  );

  // Derive accountId from stored user profile (persisted by auth slice)
  const accountId = useMemo(() => {
    try {
      const u = JSON.parse(localStorage.getItem('user') || 'null');
      return u?.id || '';
    } catch {
      return '';
    }
  }, []);

  // Filters state
  const [showFilters, setShowFilters] = useState<boolean>(false);
  // Draft (UI) filters
  const [statusSel, setStatusSel] = useState<string[]>([]);
  const [currenciesSel, setCurrenciesSel] = useState<string[]>([]);
  const [providersSel, setProvidersSel] = useState<string[]>([]);
  const [dateFrom, setDateFrom] = useState<string>('');
  const [dateTo, setDateTo] = useState<string>('');
  const [amountMin, setAmountMin] = useState<string>('');
  const [amountMax, setAmountMax] = useState<string>('');
  const [confidenceMin, setConfidenceMin] = useState<number>(0);
  // Applied filters (used for requests)
  const [aStatus, setAStatus] = useState<string[]>([]);
  const [aCurrencies, setACurrencies] = useState<string[]>([]);
  const [aProviders, setAProviders] = useState<string[]>([]);
  const [aDateFrom, setADateFrom] = useState<string>('');
  const [aDateTo, setADateTo] = useState<string>('');
  const [aAmountMin, setAAmountMin] = useState<string>('');
  const [aAmountMax, setAAmountMax] = useState<string>('');
  const [aConfidenceMin, setAConfidenceMin] = useState<number>(0);
  const [sortField, setSortField] = useState<'date' | 'amount' | 'merchant' | 'confidence'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [limit, setLimit] = useState<number>(24);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [prevCursor, setPrevCursor] = useState<string | null>(null);
  const [hasNext, setHasNext] = useState<boolean>(false);
  const [hasPrev, setHasPrev] = useState<boolean>(false);
  const [pageIndex, setPageIndex] = useState<number>(1);
  const [currentCursor, setCurrentCursor] = useState<string | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();
  const prevQRef = useRef<string>('');

  // Helpers to build URL params
  const buildParamsObj = (overrides: Record<string, any> = {}) => {
    let obj: any = {
      accountId,
      q: q || undefined,
      status: aStatus.length ? aStatus.join(',') : undefined,
      currency: aCurrencies.length ? aCurrencies.join(',') : undefined,
      provider: aProviders.length ? aProviders.join(',') : undefined,
      dateFrom: aDateFrom || undefined,
      dateTo: aDateTo || undefined,
      amountMin: aAmountMin || undefined,
      amountMax: aAmountMax || undefined,
      confidenceMin: aConfidenceMin > 0 ? aConfidenceMin : undefined,
      sort: sortField,
      order: sortOrder,
      limit,
    };
    obj = { ...obj, ...overrides };
    // Remove undefined AFTER merging, so overrides don't inject undefined keys (e.g., cursor)
    Object.keys(obj).forEach((k) => {
      if (obj[k] === undefined || obj[k] === null || obj[k] === '') delete obj[k];
    });
    return obj;
  };

  const updateUrl = (replace: boolean, overrides: Record<string, any> = {}) => {
    const obj = buildParamsObj(overrides);
    setSearchParams(obj as any, { replace });
  };

  const handleUploadClick = () => {
    navigate('/receipts/upload');
  };
  const handleManualClick = () => {
    navigate('/receipts/new');
  };

  useEffect(() => {
    const load = async () => {
      try {
        setIsLoading(true);
        if (!accountId) return;
        const r = await apiClient.searchReceiptsCursor({
          accountId,
          sort: sortField,
          order: sortOrder,
          limit,
        } as any);
        const mapped: Receipt[] = r.items.map((it: any) => ({
          id: it.id,
          filename: it.merchant,
          status: it.status as any,
          receipt_type: 'purchase',
          created_at: it.date,
          updated_at: it.date,
          file_url: it.thumbnailUrl,
          merchant_name: it.merchant,
          total_amount: String(it.amount),
          date: it.date,
          confidence_score: it.confidence,
          currency: it.currency,
          storage_provider: it.provider as any,
        }));
        setReceipts(mapped);
        setNextCursor(r.pageInfo.nextCursor);
        setPrevCursor(r.pageInfo.prevCursor);
        setHasNext(r.pageInfo.hasNext);
        setHasPrev(r.pageInfo.hasPrev);
      } catch (e: any) {
        setError(e?.message || 'Failed to load receipts');
      } finally {
        setIsLoading(false);
      }
    };
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accountId]);

  // Background check: mark receipts that already have a linked transaction
  useEffect(() => {
    let canceled = false;
    const run = async () => {
      if (!receipts.length) return;
      const idsToCheck = receipts
        .map((r) => r.id)
        .filter((id) => convertedMap[id] === undefined);
      await Promise.all(
        idsToCheck.map(async (id) => {
          try {
            const res = await apiClient.hasTransactionForReceipt(id);
            if (!canceled) {
              setConvertedMap((prev) => ({ ...prev, [id]: { exists: !!res.exists, txId: res.transaction_id } }));
            }
          } catch {
            if (!canceled) setConvertedMap((prev) => ({ ...prev, [id]: { exists: false } }));
          }
        })
      );
    };
    run();
    return () => {
      canceled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [receipts]);

  // Debounced search (query + applied filters + sorting) – resets pagination and clears cursor
  useEffect(() => {
    if (!accountId) return;
    const qTrim = q.trim();
    const prevQ = prevQRef.current;
    prevQRef.current = qTrim;
    const hasFilters =
      aStatus.length > 0 ||
      aCurrencies.length > 0 ||
      aProviders.length > 0 ||
      !!aDateFrom ||
      !!aDateTo ||
      !!aAmountMin ||
      !!aAmountMax ||
      aConfidenceMin > 0;

    // If search just cleared and no filters → restore default list via cursor API
    if (!hasFilters && qTrim.length === 0) {
      const justCleared = prevQ && prevQ.length > 0;
      if (!justCleared) return; // avoid extra fetch on first load

      // Reset pagination state
      setNextCursor(null);
      setPrevCursor(null);
      setHasNext(false);
      setHasPrev(false);
      setPageIndex(1);

      if (abortRef.current) abortRef.current.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      (async () => {
        try {
          setIsSearching(true);
          const params: any = {
            accountId,
            sort: sortField,
            order: sortOrder,
            limit,
          };
          const resp: ReceiptSearchResponseDTO = await apiClient.searchReceiptsCursor(params, controller.signal);
          const mapped: Receipt[] = resp.items.map((it) => ({
            id: it.id,
            filename: it.merchant,
            status: it.status as any,
            receipt_type: 'purchase',
            created_at: it.date,
            updated_at: it.date,
            file_url: it.thumbnailUrl,
            merchant_name: it.merchant,
            total_amount: String(it.amount),
            date: it.date,
            confidence_score: it.confidence,
            currency: it.currency,
            storage_provider: it.provider as any,
          }));
          setReceipts(mapped);
          // Prime convertedMap from API when provided
          const nextConverted: Record<string, { exists: boolean; txId?: string }> = {};
          resp.items.forEach((it) => {
            if (typeof (it as any).has_transaction === 'boolean') {
              nextConverted[it.id] = { exists: (it as any).has_transaction };
            }
          });
          if (Object.keys(nextConverted).length) setConvertedMap((prev) => ({ ...prev, ...nextConverted }));
          setNextCursor(resp.pageInfo.nextCursor);
          setPrevCursor(resp.pageInfo.prevCursor);
          setHasNext(resp.pageInfo.hasNext);
          setHasPrev(resp.pageInfo.hasPrev);
          updateUrl(true, { cursor: undefined });
        } catch (e: any) {
          if (e?.name !== 'CanceledError' && e?.code !== 'ERR_CANCELED') {
            setError(e?.message || 'Search failed');
          }
        } finally {
          setIsSearching(false);
        }
      })();
      return;
    }

    // Reset pagination cursors on new criteria
    setNextCursor(null);
    setPrevCursor(null);
    setHasNext(false);
    setHasPrev(false);
    setPageIndex(1);

    // cancel previous request
    if (abortRef.current) {
      abortRef.current.abort();
    }

    const controller = new AbortController();
    abortRef.current = controller;

    const handler = setTimeout(async () => {
      if (qTrim.length > 0 && qTrim.length < 2) return;
      try {
        setIsSearching(true);
        const params: any = {
          accountId,
          sort: sortField,
          order: sortOrder,
          limit,
        };
        if (qTrim) params.q = qTrim;
        if (aStatus.length) params.status = aStatus.join(',');
        if (aCurrencies.length) params.currency = aCurrencies.join(',');
        if (aProviders.length) params.provider = aProviders.join(',');
        if (aDateFrom) params.dateFrom = aDateFrom;
        if (aDateTo) params.dateTo = aDateTo;
        if (aAmountMin) params.amountMin = Number(aAmountMin);
        if (aAmountMax) params.amountMax = Number(aAmountMax);
        if (aConfidenceMin > 0) params.confidenceMin = aConfidenceMin;

        const run = async () => {
          const r = await apiClient.searchReceiptsCursor(params, controller.signal);
          return r;
        };
        lastActionRef.current = async () => { await run(); };
        const resp: ReceiptSearchResponseDTO = await run();
        const mapped: Receipt[] = resp.items.map((it) => ({
          id: it.id,
          filename: it.merchant,
          status: it.status as any,
          receipt_type: 'purchase',
          created_at: it.date,
          updated_at: it.date,
          file_url: it.thumbnailUrl,
          merchant_name: it.merchant,
          total_amount: String(it.amount),
          date: it.date,
          confidence_score: it.confidence,
          currency: it.currency,
          storage_provider: it.provider as any,
        }));
        setReceipts(mapped);
        const nextConverted: Record<string, { exists: boolean; txId?: string }> = {};
        resp.items.forEach((it) => {
          if (typeof (it as any).has_transaction === 'boolean') {
            nextConverted[it.id] = { exists: (it as any).has_transaction };
          }
        });
        if (Object.keys(nextConverted).length) setConvertedMap((prev) => ({ ...prev, ...nextConverted }));
        setNextCursor(resp.pageInfo.nextCursor);
        setPrevCursor(resp.pageInfo.prevCursor);
        setHasNext(resp.pageInfo.hasNext);
        setHasPrev(resp.pageInfo.hasPrev);
        // Update URL (replace while typing/searching)
        updateUrl(true, { cursor: undefined });
      } catch (e: any) {
        if (e?.name !== 'CanceledError' && e?.code !== 'ERR_CANCELED') {
          setError(e?.message || 'Search failed');
        }
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => {
      clearTimeout(handler);
      controller.abort();
    };
  }, [q, accountId, aStatus, aCurrencies, aProviders, aDateFrom, aDateTo, aAmountMin, aAmountMax, aConfidenceMin, sortField, sortOrder, limit]);

  const fetchWithCursor = async (cursor: string | null, direction: 'next' | 'prev') => {
    if (!accountId || !cursor) return;
    if (abortRef.current) abortRef.current.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    try {
      setIsSearching(true);
      const params: any = {
        accountId,
        sort: sortField,
        order: sortOrder,
        limit,
        cursor,
      };
      const run = async () => apiClient.searchReceiptsCursor(params, controller.signal);
      lastActionRef.current = async () => { await fetchWithCursor(cursor, direction); };
      const resp = await run();
      const mapped: Receipt[] = resp.items.map((it) => ({
        id: it.id,
        filename: it.merchant,
        status: it.status as any,
        receipt_type: 'purchase',
        created_at: it.date,
        updated_at: it.date,
        file_url: it.thumbnailUrl,
        merchant_name: it.merchant,
        total_amount: String(it.amount),
        date: it.date,
        confidence_score: it.confidence,
        currency: it.currency,
        storage_provider: it.provider as any,
      }));
      setReceipts(mapped);
      const nextConverted: Record<string, { exists: boolean; txId?: string }> = {};
      resp.items.forEach((it: any) => {
        if (typeof it.has_transaction === 'boolean') {
          nextConverted[it.id] = { exists: it.has_transaction };
        }
      });
      if (Object.keys(nextConverted).length) setConvertedMap((prev) => ({ ...prev, ...nextConverted }));
      setNextCursor(resp.pageInfo.nextCursor);
      setPrevCursor(resp.pageInfo.prevCursor);
      setHasNext(resp.pageInfo.hasNext);
      setHasPrev(resp.pageInfo.hasPrev);
      setPageIndex((p) => (direction === 'next' ? p + 1 : Math.max(1, p - 1)));
      // Update URL with cursor (push)
      updateUrl(false, { cursor });
    } catch (e: any) {
      if (e?.name !== 'CanceledError' && e?.code !== 'ERR_CANCELED') {
        const msg = e?.response?.data?.error === 'invalid_cursor' ? 'Page expired. Reloading results…' : (e?.message || 'Pagination failed');
        setError(msg);
        if (e?.response?.data?.error === 'invalid_cursor') {
          setNextCursor(null);
          setPrevCursor(null);
          setHasNext(false);
          setHasPrev(false);
          setPageIndex(1);
          updateUrl(true, { cursor: undefined });
        }
      }
    } finally {
      setIsSearching(false);
    }
  };

  // Apply filters (push state)
  const applyFilters = () => {
    setAStatus(statusSel);
    setACurrencies(currenciesSel);
    setAProviders(providersSel);
    setADateFrom(dateFrom);
    setADateTo(dateTo);
    setAAmountMin(amountMin);
    setAAmountMax(amountMax);
    setAConfidenceMin(confidenceMin);
    updateUrl(false, { cursor: undefined });
  };

  const toggleFromArray = (arr: string[], value: string, setter: (v: string[]) => void) => {
    if (arr.includes(value)) setter(arr.filter((v) => v !== value));
    else setter([...arr, value]);
  };

  const clearFilters = () => {
    setStatusSel([]);
    setCurrenciesSel([]);
    setProvidersSel([]);
    setDateFrom('');
    setDateTo('');
    setAmountMin('');
    setAmountMax('');
    setConfidenceMin(0);
    setAStatus([]);
    setACurrencies([]);
    setAProviders([]);
    setADateFrom('');
    setADateTo('');
    setAAmountMin('');
    setAAmountMax('');
    setAConfidenceMin(0);
    updateUrl(false, { cursor: undefined });
  };

  // Restore state from URL on first load
  useEffect(() => {
    const sp = Object.fromEntries(searchParams.entries());
    if (sp.q) setQ(sp.q);
    if (sp.sort) setSortField(sp.sort as any);
    if (sp.order) setSortOrder(sp.order as any);
    if (sp.limit) setLimit(Number(sp.limit));
    if (sp.status) { const arr = sp.status.split(',').filter(Boolean); setStatusSel(arr); setAStatus(arr); }
    if (sp.currency) { const arr = sp.currency.split(',').filter(Boolean); setCurrenciesSel(arr); setACurrencies(arr); }
    if (sp.provider) { const arr = sp.provider.split(',').filter(Boolean); setProvidersSel(arr); setAProviders(arr); }
    if (sp.dateFrom) { setDateFrom(sp.dateFrom); setADateFrom(sp.dateFrom); }
    if (sp.dateTo) { setDateTo(sp.dateTo); setADateTo(sp.dateTo); }
    if (sp.amountMin) { setAmountMin(sp.amountMin); setAAmountMin(sp.amountMin); }
    if (sp.amountMax) { setAmountMax(sp.amountMax); setAAmountMax(sp.amountMax); }
    if (sp.confidenceMin) { const v = Number(sp.confidenceMin); setConfidenceMin(v); setAConfidenceMin(v); }
    if (sp.cursor) { setCurrentCursor(sp.cursor); }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // If a cursor is present from URL on first load, fetch that page once
  const didBootstrapRef = useRef(false);
  useEffect(() => {
    if (didBootstrapRef.current) return;
    didBootstrapRef.current = true;
    if (currentCursor) {
      fetchWithCursor(currentCursor, 'next');
      setCurrentCursor(null);
    }
    // else, the debounced effect will run based on restored criteria
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentCursor]);

  // When sort/order/limit change, push state (not replace)
  useEffect(() => {
    updateUrl(false, { cursor: undefined });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sortField, sortOrder, limit]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900" id="receipts-heading">Receipts</h1>
        <div className="flex-1 mx-6 max-w-xl">
          <div className="relative">
            <input
              type="search"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search receipts (merchant, notes, number)"
              className="w-full rounded border border-gray-300 px-3 py-2 pr-10 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              aria-label="Search receipts"
            />
            {q && (
              <button
                aria-label="Clear search"
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                onClick={() => setQ('')}
              >
                ✕
              </button>
            )}
            {isSearching && (
              <div className="absolute right-8 top-1/2 -translate-y-1/2 animate-spin text-gray-400" role="status" aria-live="polite" aria-label="Searching" aria-busy="true">⏳</div>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3">
          {/* Sorting controls */}
          <div className="flex items-center gap-2">
            <label htmlFor="sortField" className="text-sm text-gray-600">Sort</label>
            <select
              id="sortField"
              value={sortField}
              onChange={(e) => setSortField(e.target.value as any)}
              className="border rounded px-2 py-1 text-sm"
              aria-label="Sort field"
            >
              <option value="date">Date</option>
              <option value="amount">Amount</option>
              <option value="merchant">Merchant</option>
              <option value="confidence">Confidence</option>
            </select>
            <button
              className="btn-outline text-sm"
              onClick={() => setSortOrder((o) => (o === 'asc' ? 'desc' : 'asc'))}
              aria-label={`Sort order ${sortOrder}`}
              title={`Order: ${sortOrder}`}
            >
              {sortOrder === 'asc' ? '⬆️ Asc' : '⬇️ Desc'}
            </button>
          </div>

          {/* Page size */}
          <div className="flex items-center gap-2">
            <label htmlFor="pageSize" className="text-sm text-gray-600">Page</label>
            <select
              id="pageSize"
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="border rounded px-2 py-1 text-sm"
              aria-label="Page size"
            >
              {[24, 36, 48, 60, 96].map((n) => (
                <option key={n} value={n}>{n}</option>
              ))}
            </select>
          </div>

          <button className="btn-secondary" onClick={handleUploadClick}>📷 Capture / Upload</button>
          <button className="btn-primary" onClick={handleUploadClick}>📤 Upload Receipt</button>
          <button className="btn-outline" onClick={handleManualClick}>➕ New (Manual)</button>
        </div>
      </div>

      {/* Live region for results summary */}
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        {isSearching ? 'Searching receipts…' : `Showing ${receipts.length} receipt${receipts.length === 1 ? '' : 's'}.`}
      </div>

      {/* Filters panel */}
      <div className="mb-4">
        <button
          className="text-sm text-indigo-600 hover:underline"
          onClick={() => setShowFilters((s) => !s)}
          aria-expanded={showFilters}
          aria-controls="filters-panel"
        >
          {showFilters ? 'Hide Filters' : 'Show Filters'}
          {(statusSel.length || currenciesSel.length || providersSel.length || dateFrom || dateTo || amountMin || amountMax || confidenceMin > 0) && (
            <span className="ml-2 text-gray-500">(active)</span>
          )}
        </button>
        {showFilters && (
          <div id="filters-panel" className="mt-3 p-4 border rounded bg-gray-50" aria-labelledby="filters-title" role="region">
            <h2 id="filters-title" className="sr-only">Filters</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Status */}
              <div role="group" aria-labelledby="filter-status">
                <div id="filter-status" className="font-medium mb-2">Status</div>
                {['processed', 'processing', 'uploaded', 'failed', 'archived'].map((s) => (
                  <label key={s} className="mr-4 inline-flex items-center gap-2 text-sm">
                    <input type="checkbox" checked={statusSel.includes(s)} onChange={() => toggleFromArray(statusSel, s, setStatusSel)} />
                    {s}
                  </label>
                ))}
              </div>

              {/* Currency */}
              <div role="group" aria-labelledby="filter-currency">
                <div id="filter-currency" className="font-medium mb-2">Currency</div>
                {['GBP', 'USD', 'EUR'].map((c) => (
                  <label key={c} className="mr-4 inline-flex items-center gap-2 text-sm">
                    <input type="checkbox" checked={currenciesSel.includes(c)} onChange={() => toggleFromArray(currenciesSel, c, setCurrenciesSel)} />
                    {c}
                  </label>
                ))}
              </div>

              {/* Provider */}
              <div role="group" aria-labelledby="filter-provider">
                <div id="filter-provider" className="font-medium mb-2">Provider</div>
                {['cloudinary', 'local'].map((p) => (
                  <label key={p} className="mr-4 inline-flex items-center gap-2 text-sm">
                    <input type="checkbox" checked={providersSel.includes(p)} onChange={() => toggleFromArray(providersSel, p, setProvidersSel)} />
                    {p}
                  </label>
                ))}
              </div>

              {/* Date range */}
              <div role="group" aria-labelledby="filter-dates">
                <div id="filter-dates" className="font-medium mb-2">Date Range</div>
                <div className="flex gap-2">
                  <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className="border rounded px-2 py-1 text-sm w-full" aria-label="From date" />
                  <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className="border rounded px-2 py-1 text-sm w-full" aria-label="To date" />
                </div>
              </div>

              {/* Amount range */}
              <div role="group" aria-labelledby="filter-amounts">
                <div id="filter-amounts" className="font-medium mb-2">Amount Range</div>
                <div className="flex gap-2">
                  <input type="number" inputMode="decimal" placeholder="Min" value={amountMin} onChange={(e) => setAmountMin(e.target.value)} className="border rounded px-2 py-1 text-sm w-full" aria-label="Min amount" />
                  <input type="number" inputMode="decimal" placeholder="Max" value={amountMax} onChange={(e) => setAmountMax(e.target.value)} className="border rounded px-2 py-1 text-sm w-full" aria-label="Max amount" />
                </div>
              </div>

              {/* Confidence */}
              <div role="group" aria-labelledby="filter-confidence">
                <div id="filter-confidence" className="font-medium mb-2">Confidence ≥ {Math.round(confidenceMin * 100)}%</div>
                <input type="range" min={0} max={1} step={0.05} value={confidenceMin} onChange={(e) => setConfidenceMin(Number(e.target.value))} className="w-full" aria-label="Minimum confidence" />
              </div>
            </div>
            <div className="mt-4 flex gap-2">
              <button className="btn-outline" onClick={clearFilters}>Clear filters</button>
              <button className="btn-primary" onClick={applyFilters} aria-label="Apply filters">Apply</button>
            </div>
          </div>
        )}
      </div>
      {/* Error banner with retry */}
      {error && (
        <div className="mb-4 p-3 border border-red-200 bg-red-50 text-red-700 rounded flex items-center justify-between">
          <span>{error}</span>
          <button
            className="btn-outline"
            onClick={async () => {
              setError(null);
              const action = lastActionRef.current;
              if (action) {
                try { setIsSearching(true); await action(); } catch { /* ignore */ } finally { setIsSearching(false); }
              } else {
                // fallback to reload initial list
                try {
                  setIsLoading(true);
                  const resp = await apiClient.getReceipts({ limit: 50, offset: 0 });
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
                    storage_provider: r.metadata?.custom_fields?.storage_provider,
                    cloudinary_public_id: r.metadata?.custom_fields?.cloudinary_public_id,
                  }));
                  setReceipts(mapped);
                } catch {}
                finally { setIsLoading(false); }
              }
            }}
          >Retry</button>
        </div>
      )}

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="card p-4 animate-pulse">
              <div className="flex items-center space-x-4">
                <div className="h-16 w-16 bg-gray-200 rounded" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-200 rounded w-3/4" />
                  <div className="h-3 bg-gray-200 rounded w-1/3" />
                </div>
                <div className="text-right">
                  <div className="h-4 bg-gray-200 rounded w-16" />
                  <div className="h-3 bg-gray-200 rounded w-10 mt-1" />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : receipts.length === 0 ? (
        <div className="card text-center py-12">
          <div className="h-16 w-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-gray-400 text-2xl">📄</span>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No results</h3>
          <p className="text-gray-500 mb-6">Try adjusting your search or clear filters.</p>
          <div className="flex items-center justify-center gap-2">
            <button className="btn-outline" onClick={() => setQ('')}>Clear search</button>
            <button className="btn-outline" onClick={clearFilters}>Clear filters</button>
          </div>
        </div>
      ) : (
        <>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" aria-busy={isSearching ? 'true' : 'false'} aria-describedby="receipts-heading">
          {receipts.map((r) => (
            <div
              key={r.id}
              className="card p-4 cursor-pointer hover:shadow"
              role="button"
              tabIndex={0}
              aria-label={`${r.merchant_name || r.filename || 'Receipt'} on ${r.date || ''}`}
              onClick={() => navigate(`/receipts/${r.id}`)}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); navigate(`/receipts/${r.id}`); } }}
            >
              <div className="flex items-center space-x-4">
                <img
                  src={r.file_url}
                  alt={r.filename}
                  className="h-16 w-16 object-cover rounded bg-gray-100"
                  onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                />
                <div className="flex-1">
                  <div className="font-semibold truncate">{r.merchant_name || r.filename}</div>
                  <div className="text-sm text-gray-500">{formatDate(r.date)}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-600">{formatCurrency(r.total_amount as any, r.currency)}</div>
                  <div className={`text-xs ${r.status === 'failed' ? 'text-red-600' : 'text-gray-400'}`}>{r.status}</div>
                </div>
              </div>
      <div className="mt-2 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  {r.status && (
                    <span className={`px-2 py-0.5 rounded border ${
                      r.status === 'failed' ? 'bg-red-50 text-red-700 border-red-200' :
                      r.status === 'processed' ? 'bg-green-50 text-green-700 border-green-200' :
                      r.needs_review ? 'bg-yellow-50 text-yellow-700 border-yellow-200' : 'bg-gray-50 text-gray-600 border-gray-200'
                    }`}>{r.status}</span>
                  )}
                  {r.confidence_score !== undefined && (
                    <span className="text-gray-500">{`conf: ${Math.round((r.confidence_score as number) * 100)}%`}</span>
                  )}
                  {r.mime_type === 'application/pdf' && (
                    <span className="px-1.5 py-0.5 rounded bg-gray-100 border border-gray-300 text-gray-700">PDF</span>
                  )}
          {r.needs_review && (
            <span className="px-2 py-0.5 rounded border bg-yellow-50 text-yellow-700 border-yellow-200">needs review</span>
          )}
          {convertedMap[r.id]?.exists && (
            <span className="px-2 py-0.5 rounded border bg-blue-50 text-blue-700 border-blue-200">Converted</span>
          )}
          {typeof (r as any).ocr_latency_ms === 'number' && (
            <span className="text-gray-400">{`${(r as any).ocr_latency_ms} ms`}</span>
          )}
                </div>
                {r.storage_provider && (
                  <span className="px-2 py-0.5 rounded bg-gray-50 border text-gray-600">
                    {r.storage_provider}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
        {/* Pagination Controls */}
        <div className="mt-4 flex items-center justify-between">
          <div className="text-sm text-gray-600" aria-live="polite">Page {pageIndex}</div>
          <div className="flex items-center gap-2">
            <button
              className="btn-outline"
              onClick={() => fetchWithCursor(prevCursor, 'prev')}
              disabled={!hasPrev || !prevCursor || isSearching}
              aria-disabled={!hasPrev || !prevCursor}
            >
              ◀ Previous
            </button>
            <button
              className="btn-outline"
              onClick={() => fetchWithCursor(nextCursor, 'next')}
              disabled={!hasNext || !nextCursor || isSearching}
              aria-disabled={!hasNext || !nextCursor}
            >
              Next ▶
            </button>
          </div>
        </div>
        </>
      )}
    </div>
  );
};

export default ReceiptsPage;