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
  - [US-006][US-008][US-009] Transactions flow: POST create succeeds and GET list contains the new item; E2E from Receipt Detail navigates to Transactions list.
  - [US-008][US-009] Transactions list totals: verify income/expense totals per currency respect active filters (date/type/category) and remain consistent across pages.
  - [US-008][US-009] Transactions list sorting/pagination: verify limit/offset/hasNext/hasPrev correctness; E2E Previous/Next keep filters/sort in URL and update results.
  - [US-008][US-009][US-010] Dashboard widgets: verify `/transactions/summary/` usage shows correct monthly Income/Expense/Net totals across currencies; add E2E.
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