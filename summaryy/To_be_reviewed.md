Phase 1 (US-005) kickoff: I verified the backend already exposes endpoints for validate/update/detail/reprocess, and the frontend OCR Results page calls the validate endpoint. To ensure persistence and visibility of review state, I updated the validation use case to set and persist a metadata.custom_fields.needs_review flag:
If the corrected OCR data validates and quality_score ≥ 0.8, needs_review = false; otherwise true.
On validation failure, we persist needs_review = true so the UI can surface it.
No linter errors introduced.
Next steps queued:
- Verify audit capture for OCR edits is present and extend coverage where needed. [US-005]
- Confirm `needs_review` badge visibility end-to-end. [US-005]
- Tests to write:
  - Validation success/failure and needs_review propagation (unit/integration). [US-005]
  - Audit creation on validate/update (UserAuditLog). [US-005]
  - Reprocess endpoint integration tests: normal path and fallback path both persist without 500s. [US-005]
  - Transactions flow: POST create succeeds and GET list contains the new item; E2E from Receipt Detail navigates to Transactions list. [US-006, US-008/009]