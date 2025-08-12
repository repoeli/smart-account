Phase 1 (US-005) kickoff: I verified the backend already exposes endpoints for validate/update/detail/reprocess, and the frontend OCR Results page calls the validate endpoint. To ensure persistence and visibility of review state, I updated the validation use case to set and persist a metadata.custom_fields.needs_review flag:
If the corrected OCR data validates and quality_score ≥ 0.8, needs_review = false; otherwise true.
On validation failure, we persist needs_review = true so the UI can surface it.
No linter errors introduced.
Next steps queued:
- [US-005] Verify audit capture for OCR edits is present and extend coverage where needed.
- [US-005] Confirm `needs_review` badge visibility end-to-end.
- Tests to write:
  - [US-005] Validation success/failure and needs_review propagation (unit/integration).
  - [US-005] Audit creation on validate/update (UserAuditLog).
  - [US-005] Reprocess endpoint integration tests: normal path and fallback path both persist without 500s.
  - [US-005] Reprocess audit: assert `UserAuditLog` row created with `event_type='receipt_reprocess'` and expected payload (engine/success/latency_ms/error).
  - [US-004] Storage migration: POST `/receipts/{id}/storage/migrate/` uploads to Cloudinary and updates telemetry; assert local `/media/...` and remote URLs both succeed; verify `file_url` becomes Cloudinary `secure_url` and `cloudinary_public_id` populated.
  - [US-004][US-005] Replace file flow: POST `/receipts/{id}/replace/` accepts image/PDF multipart; on success, `file_url` updated (Cloudinary), telemetry populated; when `reprocess=true` (default), OCR data persisted or `needs_review` set; audit row `receipt_replace` created.
  - [US-004] SHA-256 integrity: assert checksum is stored on upload/replace; optional test to compare client-computed checksum vs stored.
  - [US-005] Reprocess history endpoint: GET `/receipts/{id}/reprocess/history/?limit=10` returns latest entries; verify shape `{at, engine, success, latency_ms?, error?}` and ordering desc.
  - [US-005] Audit logs endpoint: GET `/audit/logs/?eventType=receipt_validate` returns recent logs; filter by `receipt_id` works; pagination (limit) respected.
  - [US-005] OCR health: GET `/ocr/health/` returns structured status; mock up/down states; ensure latency fields present (optional snapshot tolerance).
  - [US-006][US-008][US-009] Transactions flow: POST create succeeds and GET list contains the new item; E2E from Receipt Detail navigates to Transactions list.
  - [US-008][US-009] Transactions list totals: verify income/expense totals per currency respect active filters (date/type/category) and remain consistent across pages.
  - [US-008][US-009] Transactions list sorting/pagination: verify limit/offset/hasNext/hasPrev correctness; E2E Previous/Next keep filters/sort in URL and update results.
  - [US-008][US-009] Transactions filter chips: verify removing chips updates URL and results; Clear-all resets offset and empties chips; totals banner always present.
  - [US-008][US-009][US-010] Dashboard widgets: verify `/transactions/summary/` usage shows correct monthly Income/Expense/Net totals across currencies; add E2E.
  - [US-010] Summary grouping by month: regression test for `TruncMonth` output being `date` vs `datetime` (no AttributeError); verify keys are `YYYY-MM`.
  - [US-010] Dashboard summary retry: simulate first 500 then 200; verify UI shows banner then recovers after retry; “Retry” button triggers reload.
  - [US-010] KPI trend: with synthetic data, verify previous-period comparison computes correct diff for Income, Expense, and Net.
  - [US-005] Dashboard OCR health pill: mock up/down states and ensure pill text/color reflect engine availability.
  - [US-006] Categories: E2E category dropdown hydrates from `/categories/`, falls back gracefully; ensure selected category filters list and persists via URL/localStorage.
  - [US-008][US-009] Receipt→Transaction 1:1 guard (no duplicates):
    - UI: disable "Create Transaction" button on `ReceiptDetailPage` when a transaction already exists for the receipt; surface a tooltip/explanatory note. Do NOT change DB yet.
    - API option (preferred, no DB change): support `GET /transactions/?receipt_id=<id>&limit=1` to check existence; or include `has_transaction` in `GET /receipts/:id`. Decide one path and implement.
    - E2E: create once → button disabled on reload; attempting again does nothing; transactions list remains single entry.
    - Later (DB hardening): add unique partial index on `transactions(receipt_id)` WHERE receipt_id IS NOT NULL. Migration + backfill/validation. [US-008][US-009]
    - UX enhancement: Receipts list should display a small “Converted” badge for receipts with an existing transaction. Current implementation performs per-card background checks; optimize by enriching list API items with `has_transaction` to avoid N queries. Document API shape and add caching where appropriate.
  - [US-008][US-009] Inline category edit (Transactions):
    - Backend: ensure PATCH `/transactions/:id` supports updating `category` with ownership checks and returns `{success}`.
    - Frontend: inline editor should optimistically update and rollback on error; dropdown hydrates from `/categories/` with fallback to free-text when not available.
  - [US-008][US-009] Tests: Backend `receipt_id` filter → verify 0/1 results on `/transactions/?receipt_id=<id>`; include mixed dataset cases.
  - [US-008][US-009] Tests: Frontend E2E → Create transaction from Receipt Detail, reload detail, assert “Create Transaction” is disabled and shows explanatory note; verify only one row appears in `/transactions`.
  - [US-008][US-009] Optional UX: show a small “Converted” badge on receipts that already have a transaction. Implement via detail enrichment (`has_transaction`) or list-row check using `/transactions/?receipt_id` on demand.

- [US-010] Dashboard Phase – next big tasks
  - Add date range presets (This month, Last month, This year, Custom) controlling `/transactions/summary/` queries.
  - Extend summary API to support `groupBy=month|category|merchant` and return time-series suitable for charts. [US-008][US-009][US-010] (implemented: merchant; tests pending)
  - Frontend charts: income vs expense over time (line/area), category breakdown (pie/donut), top merchants (bar). [US-010]
  - Performance (NFR): cache summary responses server-side (e.g., 60s in-memory) and ensure p95 < 300ms; add simple timing logs. [US-010]
  - Tests: backend summary grouping/caching; frontend E2E to validate filters reflect in charts and totals. [US-010]
  - Tests: Dashboard custom date range presets persist across reload; summary reflects selected dates; error banner shown on 500s.
  - Tests: Transactions list timing logs do not alter response; totals remain consistent with filters.