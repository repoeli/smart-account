### Smart Accounts – Work Completed Since Last Commit

#### New (US-004, US-005, US-010)
- Backend
  - [US-004][US-005] Added POST ` /api/v1/receipts/{id}/storage/migrate/ ` to move an existing local/remote asset to Cloudinary. Persists `metadata.custom_fields.storage_provider='cloudinary'` and `cloudinary_public_id`, and updates `file_url` to the Cloudinary `secure_url`. Handles local relative `/media/...` and remote download cases.
  - [US-005] Added GET ` /api/v1/ocr/health/ ` reporting Paddle FastAPI and OpenAI availability with latency; non-invasive and cached by browser naturally.
  - [US-005] Hardened OCR pipeline: always attempt Paddle HTTP (by-URL → by-file) before OpenAI, then legacy. Normalizes relative URLs to absolute using `PUBLIC_BASE_URL` so OCR services can fetch images reliably.
  - [US-005] Validate fallback improved to persist edits (including currency) and avoid 500s while marking `needs_review=true` if strict validation fails.
  - [US-004][US-005] Added POST ` /api/v1/receipts/{id}/replace/ ` to upload a new file for an existing receipt (Cloudinary-first) and optionally reprocess. Persists storage telemetry and updates `file_url`.
  - [US-004] File integrity: compute and store `metadata.custom_fields.sha256` on upload/replace for integrity tracing.
  - [US-005] Added GET ` /api/v1/audit/logs/ ` to list recent `UserAuditLog` entries with optional `eventType` and `receipt_id` filters.
  - [US-010] Fixed dashboard summary 500 for `groupBy=month,category,merchant`. `TruncMonth(...)` can return a `date`; we now build month keys with `strftime('%Y-%m')` for both `date` and `datetime` objects.

- Frontend
  - [US-005] `ReceiptDetailPage.tsx`: added OCR status pill (green Paddle, yellow OpenAI, red Unavailable) using the new health endpoint; tooltip shows latencies.
  - [US-004] Added “Move to Cloudinary” button when storage is not Cloudinary; calls `migrateReceiptToCloudinary` and refreshes detail on success.
  - [US-004][US-005] Added “Replace File” control on `ReceiptDetailPage` (accepts image/PDF). On success, refreshes receipt and triggers reprocess by default.
  - [US-005] `ReceiptDetailPage` shows a lightweight Reprocess History list populated from `/receipts/{id}/reprocess/history/`.
  - [US-004] `ReceiptDetailPage` surfaces file integrity with a checksum (SHA-256) display and copy-to-clipboard.
  - [US-005] OCR Results edit form now uses DD/MM/YYYY text input; Save includes `currency` and normalizes date formats; Create Transaction guarded until amount/date are valid.
  - [US-005] `api.getReceipt` normalizes relative `file_url` to absolute so previews and Copy URL work even for local storage.
  - [US-010] Dashboard: added a safe retry with backoff for `GET /transactions/summary/` and a Retry button in the banner to recover gracefully from transient errors.

- Configuration
  - [US-004] If using local storage in dev, set `PUBLIC_BASE_URL=http://127.0.0.1:8000` so newly saved local files get absolute URLs.

#### Impact
- Reprocess and validate flows are resilient; images reliably reach OCR services; UI remains responsive (no full page reloads) and shows engine availability.
- Dashboard summary loads without 500s; empty datasets render cleanly.
 - Dashboard handles transient failures with a quick retry and user-invoked Retry.

#### Minor
- [US-005] Reprocess actions now write an audit entry (`receipt_reprocess`) with `{engine, success, latency_ms?, error?}`.


#### Overview
- Implemented Cloudinary-first storage for receipt uploads with resilient local fallback.
- Stabilized OCR flow to prefer the running Paddle FastAPI service (HTTP adapter) and reduced over‑strict validation that caused false failures.
- Tightened environment/config loading so your backend/.env is always respected.

- Transactions list enhanced end-to-end: server-side filters/sorting, totals by currency, pagination metadata; frontend controls with URL sync, Intl currency formatting, and links back to source receipts.

#### Backend changes (files edited)
- `backend/application/receipts/use_cases.py`
  - Cloudinary‑first upload: now uses `CloudinaryStorageAdapter.upload(file_bytes=..., resource_type=auto)` when Cloudinary keys are present; persists `secure_url` as `file_url`.
  - If Cloudinary fails, automatically falls back to local storage and surfaces a combined error string (for diagnostics) if that also fails.

- `backend/infrastructure/storage/adapters/cloudinary_store.py`
  - Set `resource_type="auto"` (uploads PDFs/WEBP/etc). Still returns a `StoredAsset` with `secure_url` used by the UI.

- `backend/infrastructure/storage/services.py` (pre‑existing)
  - Local fallback path remains; returns absolute URL using `PUBLIC_BASE_URL`.

- `backend/smart_accounts/settings/base.py`
  - Explicitly loads `backend/.env` so env vars are reliably picked up in dev.
  - `CLOUDINARY_RECEIPTS_FOLDER` also honors `CLOUDINARY_UPLOAD_FOLDER`.
  - Confirmed existing OCR/Storage env mapping (`OCR_ENGINE_DEFAULT`, `PADDLE_API_BASE`, etc.).

- `backend/infrastructure/ocr/services.py`
  - For URL‑based OCR, prefer `PaddleOCRHTTPAdapter` (FastAPI microservice) and map the response into domain `OCRData` (merchant, totals, currency, raw_text, latency, etc.).
  - Preserved OpenAI Vision and legacy fallbacks.

- `backend/domain/receipts/services.py`
  - `FileValidationService`: now uses `MAX_RECEIPT_MB` from settings and allows `application/pdf` (US‑004 acceptance). 
  - `ReceiptValidationService`: lowered `min_confidence_threshold` to 0.2 so low‑confidence OCR results don’t hard‑fail; they remain editable in the UI.

#### API/UX impact
- New uploads will be sent to Cloudinary (when keys exist) and `file_url` will be a Cloudinary HTTPS URL, so thumbnails render directly from the CDN.
- Receipts no longer default to failed solely due to low confidence; processing status should move to processed with data populated (merchant/date/total) when available.

- Transactions now supports practical ledger exploration: filter by date/type/category, sort by date/amount/category, view income/expense totals grouped by currency, and paginate through large lists without losing filter context.

#### Configuration expectations
- Ensure in `backend/.env`:
  - `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`
  - Optional: `CLOUDINARY_RECEIPTS_FOLDER` or `CLOUDINARY_UPLOAD_FOLDER`
  - `OCR_ENGINE_DEFAULT=paddle`, `PADDLE_API_BASE=http://127.0.0.1:8089`
  - `MAX_RECEIPT_MB=10`, `PUBLIC_BASE_URL=http://127.0.0.1:8000`

#### How to verify quickly
1. Restart Django to load `.env`.
2. Upload a JPG/PNG/PDF via the app.
3. In the Receipts list, the thumbnail should come from `https://res.cloudinary.com/...` and status should be processed (or at least not failed).
4. In Cloudinary console, the file should appear under the configured folder (default `receipts`).
5. If OCR output seems off, reprocess a receipt: `POST /api/v1/receipts/{id}/reprocess/ {"ocr_method":"paddle_ocr"}`.

6. Create a transaction from a receipt (Receipt Detail → Create Transaction). You should be redirected to `/transactions` and see the new row.
7. On `/transactions`, adjust Date/Type/Category and Sort controls; rows and totals should update; URL should reflect state.
8. Use Previous/Next to paginate; the range and total count update, and filters remain applied.

#### Backend changes (Transactions)
- `backend/interfaces/api/views.py`
  - `GET /api/v1/transactions/` now supports:
    - Filters: `dateFrom`, `dateTo`, `type`, `category`
    - Sorting: `sort` in {date, amount, category}, `order` in {asc, desc}
    - Pagination: `limit`, `offset` and returns `page` object: `{limit, offset, totalCount, hasNext, hasPrev}`
    - Totals: `totals` object containing `income` and `expense` arrays grouped by `currency`, with decimal-safe sums.
    - Optional filter: `receipt_id=<uuid>` to fetch transactions for a specific receipt (used by UI to guard 1:1 create).
  - Still returns each item with `merchant` resolved from linked `Receipt` (if any) for quick context.

#### Frontend changes (Transactions)
- `frontend/src/pages/TransactionsPage.tsx`
  - Added filter controls (date range, type, category) and sort controls with asc/desc toggle.
  - Added totals banner (income/expense by currency) with Intl.NumberFormat for currency display.
  - Added pagination controls (Previous/Next) using `limit`/`offset` and shows a results range summary.
  - Keeps state in URL (`useSearchParams`) so share/refresh preserves the current view.
  - Merchant names link back to the source `receipts/:id` when a receipt is attached.
  - Added optional category dropdown fed by `/api/v1/categories/`; falls back to free-text.
  - Introduced a small TypeScript `TransactionCategory` union for better DX and type safety across the app.
  - UI 1:1 guard: on `ReceiptDetailPage` the “Create Transaction” button is disabled if `/transactions/?receipt_id=<id>&limit=1` returns an item; shows “Already converted”. No DB constraint yet.
  - [US-008][US-009] Polish: totals banner always renders (zeros fallback) to avoid layout shift, quick filter chips with remove/clear-all, clearer empty state (“No results for selected filters”).

#### Frontend changes (Dashboard)
- `frontend/src/pages/DashboardPage.tsx`
  - Uses `/api/v1/transactions/summary/` to display current month totals: Income, Expenses, and Net per currency, formatted via Intl.
  - Added simple charts for by-month and category breakdown; added Top Merchants chart using new `groupBy=merchant` support.
  - Added error banner to gracefully handle summary load failures; falls back to empty visuals.
  - Added date range presets with Custom option (date pickers) and persisted selection to `localStorage`.
  - [US-010] Added a single safe retry with a Retry button for summary loading; added trend lines on KPI cards comparing to previous period.
  - [US-005] Dashboard shows OCR engine status pill (Paddle/OpenAI/Unavailable) using `/ocr/health/` for quick visibility.

#### Notes
- A “PaddleOCR not available” warning can still appear from the in‑process initializer; the actual OCR path uses the FastAPI HTTP service when running.



#### New since last push
- Backend
  - Transactions summary: added `groupBy=merchant`, added timing logs, and made cache TTL configurable via `SUMMARY_CACHE_TTL` (default 60s).
  - Transactions list: added timing logs for performance tracking.
  - Receipts upload: hardened `POST /api/v1/receipts/upload/` with a last-resort fallback that saves the file (Cloudinary or local) and persists a minimal `Receipt` row to avoid 500s; includes storage telemetry in `metadata.custom_fields`.
  - Receipt telemetry: persist `metadata.custom_fields.storage_provider` and `metadata.custom_fields.cloudinary_public_id` on upload (Cloudinary vs local visibility per receipt).
  - Added diagnostics API `GET /api/v1/files/info/?url=...` to verify Cloudinary/local assets and return metadata (public_id, format, width/height, bytes, created_at).
  - Relaxed receipt ownership checks in development for detail/update/reprocess/validate flows to prevent 400s while data is normalized.
  - Reprocess behavior: always persist OCR data on success. If validation fails, mark `needs_review=true` and attach `validation_errors` instead of returning 400; response includes `warnings`.

- Frontend
  - TransactionsPage: Inline category editor with optimistic update + toasts; PATCH to `/transactions/:id` wired.
  - ReceiptsPage: Converted badge now hydrated via `has_transaction` from list API.
  - ReceiptUploadPage: improved error messaging to inform about potential fallback save; advises user to check Receipts list and reprocess if needed.
  - Receipts list (`ReceiptsPage.tsx`): shows storage origin badge (cloudinary/local) and OCR confidence percentage. Mapping updated to read `metadata.custom_fields`.
  - Receipt detail page (`ReceiptDetailPage.tsx`): implemented fully. Displays thumbnail, merchant, total, date, confidence, storage provider, Cloudinary public_id. Adds actions to reprocess with Paddle or OpenAI and to open the OCR results page.
  - API client (`api.ts`): `getReceipt` now normalizes backend shape (nested `ocr_data`, `metadata.custom_fields`) into the frontend `Receipt` type.
  - Types (`types/api.ts`): aligned `receipt_type` union with backend; added optional `storage_provider` and `cloudinary_public_id` fields.

- Settings/Config
  - Ensured `.env` is loaded from `backend/.env` explicitly.
  - `CLOUDINARY_RECEIPTS_FOLDER` also reads `CLOUDINARY_UPLOAD_FOLDER` if present.

- Impact
  - New uploads render from Cloudinary with visible provenance; details and reprocess actions work without 400s. Low‑confidence OCR is saved and flagged for review rather than failing.

- Follow‑ups proposed
  - Header auth UI hydration: derive visibility from successful `getCurrentUser()` after refresh to keep logout/menu consistent.
  - Optional: “View on Cloudinary” link using `cloudinary_public_id` on detail page; display OCR latency and needs‑review badges.

#### New since last commit (Camera capture stabilization)
- Frontend – camera capture refactor (durable, race‑free)
  - Added reusable hook `frontend/src/hooks/useUserMedia.ts`:
    - Globally caches a single `MediaStream` and uses reference counting to survive React StrictMode double‑mount/unmount.
    - Prevents repeated permission prompts and avoids play/pause races by returning an already‑active stream to consumers.
    - Graceful shutdown: when the last consumer releases, all tracks are stopped after a short grace period.
  - Refactored `frontend/src/pages/receipts/ReceiptUploadPage.tsx`:
    - Inline camera renders inside the rectangle (no modal). `CameraCapture` uses `useUserMedia` and attaches the stream once.
    - Device selection: enumerates `videoinput` devices and allows switching via dropdown; prefers back/environment camera by default.
    - Frame detection: listens for `loadeddata`/`canplay` and surfaces an overlay if frames don’t arrive (some drivers report active camera but deliver black frames).
    - Native fallback: adds “Use System Camera” button (`<input type="file" accept="image/*" capture="environment">`) that opens the OS camera and returns a captured image when direct stream preview isn’t possible.
    - Cleanup: on close/unmount, removes listeners, clears `srcObject`, pauses video and stops tracks from the cached stream when no other consumers exist.
    - Removed auto‑retry loops that caused `AbortError: play() request was interrupted by a new load request` spam; replaced with deterministic attach + single play().
    - Keeps capture quality reasonable (720p target via device defaults) and relies on browser downscaling; no hard constraints that break embedded webcams.

- UX/QA notes
  - Expected behavior: camera light turns on; inline preview shows. If a given device (driver/privacy mode) provides no frames, the overlay appears and native capture path is available so users can proceed immediately.
  - Verified that closing the camera or navigating away releases tracks; no lingering camera indicator after a short grace period.

- Test guidance
  1. Open Upload Receipts → Open Camera. Confirm live preview or overlay + fallback button.
  2. Switch devices via dropdown if multiple cameras exist; verify preview updates without permission re‑prompt.
  3. Click Close Camera; browser camera indicator should turn off shortly. Re‑open to confirm re‑attachment works.
  4. Use “Use System Camera”, capture, and check that the photo is added to the upload list and can be uploaded end‑to‑end.

### Task 1 (Backend API View)  In Progress
- Implemented enhanced GET /api/receipts in ReceiptListView to support search filters, sorting, and cursor-based pagination with stable (field, id) tie-break.
- Added server-side validation via ReceiptSearchRequestSerializer.
- Mapped filter fields to ORM JSON fields (ocr_data, metadata.custom_fields).
- Replaced deprecated .extra() usage with proper Django ORM comparisons for cursor filters.
- Kept legacy offset-based path for backward compatibility.
- Next: wire URL if needed (already mapped to ReceiptListView), basic manual tests, and finalize response mapping parity with frontend expectations.

### Task 3 (Frontend Search Input & Debouncing)  In Progress
- Added cursor search types in  frontend/src/types/api.ts and API method searchReceiptsCursor with AbortController support.
- Implemented search input on  frontend/src/pages/ReceiptsPage.tsx with 300ms debounce, inflight cancellation, spinner, and clear button.
- Search uses GET /api/v1/receipts with  accountId, q, sort, order, limit; maps results to existing card UI.
- Next: integrate URL state sync and more filters in subsequent tasks.

### Task 3  Completed; Task 4  In Progress
- Task 3 complete: Implemented debounced search input with cancellation, spinner, and clear, wired to GET /receipts (cursor).
- Began Task 4: Added collapsible filters panel (status, currency, provider, date range, amount range, confidence slider). Filters feed into debounced request.
- Next: Task 4 polish (chip indicators, a11y labels reviewed, minor layout refinements).

### Task 5 (Sorting & Pagination)  Completed
- Added sort field dropdown and order toggle with debounce reset.
- Implemented page size selector.
- Implemented Previous/Next using cursors from backend response; disables when unavailable; shows current page.
- All tied into debounced request and AbortController cancellation.

### Task 7 (UI States & Error Handling)  Completed
- Added skeleton loaders for initial loading.
- Implemented error banner with Retry (replays last action or reloads).
- Added robust handling for invalid cursors by resetting pagination and URL.
- Added No results state with Clear search and Clear filters actions.

### Task 8 (A11y & i18n)  Completed
- Added ARIA labels, roles, and live regions for search, results, and filters.
- Enabled keyboard navigation for receipt cards (Enter/Space).
- Localized currency and dates using Intl with user locale fallback.
- Grid marks aria-busy during searches.

---

### Updates – Search & OCR Results (Completed)

#### Delivered
- Debounced, cancelable search with URL sync and cursor pagination on `ReceiptsPage`.
- OCR Results page is fully usable: manual edit/save with server validation, reprocess, and fixed display.
- Search backend hardened with stable cursor semantics and safe JSON handling.

#### Frontend tasks
- Receipts search
  - 300ms debounce, `AbortController` cancellations, spinner, and clear button.
  - URL synchronization for `q|filters|sort|order|limit|cursor` with replace while typing and push on actions.
  - Cursor pagination (Prev/Next) wired to backend `nextCursor/prevCursor`; page index and disabled states.
  - Clear‑search behavior: when input transitions from non‑empty to empty (and no filters), fetch base list immediately, reset cursors/page, replace URL.
  - Error banner with Retry that replays the last action or reloads a base list.
- OCR Results page
  - Route param fix: uses `useParams<{ id: string }>()` to match `/receipts/:id/ocr`.
  - Loads receipt via `getReceipt` and maps to editable OCR fields.
  - Save uses `validateReceipt(id, payload)`; converts date from `YYYY-MM-DD` to `DD/MM/YYYY`.
  - Confidence UI: normalize 0–1 or 0–100 into 0–1, clamp, overflow‑safe progress bar.

#### Backend search fixes (recap)
- Dynamic import of `KeyTextTransform` (modern and legacy paths); guarded PG path with Python fallback when unavailable.
- Avoid JSON date casts; use `created_at` for date sorting and filtering.
- Stable seek pagination by `(sortValue, id)` with proper inequality per order.
- Request validation and limit clamping via `ReceiptSearchRequestSerializer`.

#### Issues encountered → fixes
- 500 errors on search with `q`
  - JSON casting and `KeyTextTransform` import differences; brittle JSON date casting.
  - Fixed with dynamic import, guarded PG‑only path, in‑memory fallback, and `created_at` date handling.
- ImportError for `KeyTextTransform`
  - Module moved across Django versions.
  - Fixed by attempting `django.db.models.fields.json` first, then legacy path; fallback if missing.
- Search state ignored / account scoping wrong
  - `accountId` not passed consistently; URL had empty params including `cursor`.
  - Fixed by deriving from `localStorage.user.id`; stripping empty params; adding `cursor` only while paging.
- Clearing search didn’t restore list
  - Debounced effect returned early when `q === ''`.
  - Fixed by tracking previous query; on non‑empty → empty, fetch base list and reset cursors/page.
- JSX parse error on grid
  - Two sibling nodes without wrapper.
  - Fixed by wrapping grid and pagination with a fragment.
- OCR Results stuck on loading
  - Route param mismatch (`receiptId` vs `id`).
  - Fixed by switching to `id` in `useParams`.
- Confidence bar overflow
  - Confidence sometimes 0–100; UI assumed 0–1.
  - Fixed by normalization and clamping; container `overflow-hidden`.

#### Key files touched (high signal)
- Frontend: `frontend/src/pages/ReceiptsPage.tsx`, `frontend/src/pages/receipts/OCRResultsPage.tsx`, `frontend/src/components/receipts/OCRResults.tsx`, `frontend/src/pages/ReceiptDetailPage.tsx`.
- Backend: `backend/interfaces/api/views.py` (search executor), `backend/infrastructure/pagination/cursor.py` (cursor), `backend/infrastructure/database/migrations/0003_search_indexes.py` (indexes).

#### Verification
- Search: type ≥2 chars → results update; clear input (no filters) → default list, page reset; Prev/Next using cursors; URL reflects state.
- OCR: open from details, edit fields, Save (server validates/persists), confidence shows correctly without overflow, Reprocess works.
 - Transactions: create via Receipt Detail → success toast → redirected to Transactions page → new row visible.

---

### Phase 2 – One‑click Transaction + Category Suggestions (Planned split)

Sprint 2.1 (Backend foundations)
- Domain: add Transactions entities/repository (domain layer) and application `CreateTransactionUseCase` (done: scaffolding created; no integration yet).
- Persistence: introduce infrastructure repo + Django model/migration (next).
- API: POST /api/v1/transactions (create), GET /api/v1/categories (list), GET /api/v1/categories/suggest?receiptId=… (next).

Sprint 2.2 (Frontend CTA + flow)
- Add “Create Transaction” button on receipt detail / OCR page, prefilled with merchant/date/amount/currency; category suggestion call; submit to create.
- Confirm success path navigates to Transactions list with snackbar.

Sprint 2.3 (Quality)
- Tests: unit (suggestion), integration (create from receipt), E2E happy path.
- Perf: indexes on transactions per ERD; basic metrics.

Constraints
- Respect SoC: keep domain/app/infrastructure/interfaces layers separate; avoid perturbing existing receipts flows.
- Backwards compatible migrations; feature‑flag if needed.

User Stories mapping
- US‑006 (Categorization) & US‑008/009 (Finance): transaction creation from receipt; suggestions.

---

### User Stories Mapping (for this update)
- US-007: Receipt Search and Filtering — Status: Completed (this iteration)
  - Debounced merchant search with cancelation, URL sync, cursor-based pagination, clear-search restores default list, sorting and page size, error states, a11y live regions.
- US-005: OCR Receipt Processing — Status: Completed (this iteration)
  - "Open OCR Results" page functional; manual edit and save via server validation; reprocess action; normalized confidence display (no overflow).
- US-004: Receipt Upload — Status: Improved (partial)
  - Cloudinary-first storage with local fallback, camera capture stabilization, file validation improvements, telemetry and diagnostics.
  - Remaining (not in this update): richer progress UI, batch/multi uploads, broader file types/limits per spec.
- NFRs: Accessibility & Internationalization — Status: Completed (for Receipts and OCR screens)
  - ARIA labels/live regions, keyboard navigation, localized currency/dates.

---

### Phase 1 – OCR Editing & Audit (In Progress)

- Backend
  - Persisted review state: `ReceiptValidateUseCase` now sets `metadata.custom_fields.needs_review`.
    - Logic: needs_review = true when validation fails or `quality_score < 0.8`; false when high quality.
    - Always persisted so the UI can reliably surface a “needs review” badge.
  - Audit logging for edits/updates:
    - `ReceiptValidateView` and `ReceiptUpdateView` create `UserAuditLog` entries (user, receipt_id, payload, result, IP, user agent).
- Frontend
  - Reads `needs_review` from receipt metadata; confirm badge visibility across Receipts list and Receipt detail.
- Files changed
  - `backend/application/receipts/use_cases.py` (update `ReceiptValidateUseCase`).
  - `backend/interfaces/api/views.py` (add audit writes in validate and update views).
- Test plan (pending)
  - Unit: validation success/failure → needs_review true/false; quality threshold behavior.
  - Integration: validate API persists flag; audit row created; round‑trip visible via GET detail.
- User Stories mapping
  - US‑005 (OCR Receipt Processing): edit, validate, reprocess flows; review state persisted.
  - NFR (Auditability): user edit actions are captured with context for traceability.

---

### Phase 2 – Sprint 2.2 (Frontend CTA + Flow) – In Progress

- What’s done
  - API client additions: `createTransaction(...)`, `suggestCategory(...)` (graceful fallback if backend not ready).
  - Receipt detail UI: added “Create Transaction” action.
    - Prefills: description from merchant, amount/currency/date from OCR, receipt_id attached.
    - Fetches category suggestion (if available) and submits to create.
    - Success/error toasts.
- To do (this sprint)
  - Backend endpoints: POST `/api/v1/transactions` and GET `/api/v1/categories/suggest` (map to new use case + repo once infra model exists).
  - Frontend: Transactions list page (minimal stub) and navigation after create.
  - Tests: happy path E2E for CTA; integration once backend endpoint lands.
- Guardrails
  - Non‑breaking: client gracefully no‑ops if suggestion endpoint missing; create surfaces backend errors.
- User Story mapping
  - US‑006, US‑008/009 (Categorization & Finance): one‑click create with suggested category.

---

### Phase 2 – Sprint 2.2 (Backend persistence + UI nav) – Progress

- Backend
  - Added Django model `transactions` with indexes (user, date, type, category).
  - Implemented infrastructure repo `DjangoTransactionRepository` and wired POST `/api/v1/transactions` to `CreateTransactionUseCase`.
- Frontend
  - Receipt Detail “Create Transaction” now calls real endpoint.
  - Added Transactions list page and navigation after success.
  - Added UI 1:1 guard on the list: Receipts grid shows a "Converted" badge for receipts that already have a linked transaction. This currently performs a lightweight background check per visible receipt via `GET /api/v1/transactions/?receipt_id=<id>&limit=1`; planned optimization is to enrich list items with `has_transaction` from the backend.
  - Inline category edit on `TransactionsPage.tsx` with optimistic update and server PATCH; dropdown hydrates from `/api/v1/categories/` when available.
- Tests (next)
  - Integration: POST create returns transaction_id and persists; GET list shows it.
  - E2E: click CTA → success toast → redirected to list with new row.
  - Verify receipts grid shows “Converted” for already-converted receipts and that the `ReceiptDetailPage` shows “Already converted · View transaction”.
- User Story mapping
  - US‑006, US‑008/009 – persistence of transactions and creation from receipt now functional.
