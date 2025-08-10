Phase 1 (US-005) kickoff: I verified the backend already exposes endpoints for validate/update/detail/reprocess, and the frontend OCR Results page calls the validate endpoint. To ensure persistence and visibility of review state, I updated the validation use case to set and persist a metadata.custom_fields.needs_review flag:
If the corrected OCR data validates and quality_score ≥ 0.8, needs_review = false; otherwise true.
On validation failure, we persist needs_review = true so the UI can surface it.
No linter errors introduced.
Next steps I will do next turn unless you want adjustments:
Add audit capture for OCR edits (who/when/what changed) using an audit event or UserAuditLog.
Ensure the ReceiptDetail and Receipts list surface the needs_review badge consistently (frontend already reads it; I’ll double-check).
Add unit/integration tests around validation success/failure and needs_review propagation. [US-005]
Add unit/integration tests for audit creation on validate/update (UserAuditLog). [US-005]