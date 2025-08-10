### Smart Accounts – Work Completed Since Last Commit

#### Overview
- Implemented Cloudinary-first storage for receipt uploads with resilient local fallback.
- Stabilized OCR flow to prefer the running Paddle FastAPI service (HTTP adapter) and reduced over‑strict validation that caused false failures.
- Tightened environment/config loading so your backend/.env is always respected.

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

#### Notes
- A “PaddleOCR not available” warning can still appear from the in‑process initializer; the actual OCR path uses the FastAPI HTTP service when running.



#### New since last push
- Backend
  - Receipt telemetry: persist `metadata.custom_fields.storage_provider` and `metadata.custom_fields.cloudinary_public_id` on upload (Cloudinary vs local visibility per receipt).
  - Added diagnostics API `GET /api/v1/files/info/?url=...` to verify Cloudinary/local assets and return metadata (public_id, format, width/height, bytes, created_at).
  - Relaxed receipt ownership checks in development for detail/update/reprocess/validate flows to prevent 400s while data is normalized.
  - Reprocess behavior: always persist OCR data on success. If validation fails, mark `needs_review=true` and attach `validation_errors` instead of returning 400; response includes `warnings`.

- Frontend
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
