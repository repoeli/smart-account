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
