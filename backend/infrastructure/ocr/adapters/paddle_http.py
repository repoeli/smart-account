"""
HTTP adapter for PaddleOCR FastAPI microservice.
Reads service URLs from environment and maps responses into ReceiptExtraction.
"""

from __future__ import annotations

import os
import time
import logging
from typing import Optional, Dict, Any

import requests
from django.conf import settings

from application.receipts.ports import OCRProvider, ReceiptExtraction

logger = logging.getLogger(__name__)


class PaddleOCRHTTPAdapter(OCRProvider):
    def __init__(self):
        self.url_file = os.getenv("PADDLE_OCR_URL", getattr(settings, "PADDLE_OCR_URL", "http://127.0.0.1:8089/ocr/receipt"))
        self.url_by_url = os.getenv("PADDLE_OCR_URL_BY_URL", getattr(settings, "PADDLE_OCR_URL_BY_URL", "http://127.0.0.1:8089/ocr/receipt-by-url"))
        self.timeout = int(os.getenv("OCR_TIMEOUT_SECONDS", getattr(settings, "OCR_TIMEOUT_SECONDS", 25)))
        self.retries = 3

    def _map(self, payload: Dict[str, Any], source_url: Optional[str], latency_ms: int) -> ReceiptExtraction:
        return ReceiptExtraction(
            engine="paddle",
            merchant=payload.get("merchant"),
            date=payload.get("date"),
            total=payload.get("total"),
            currency=payload.get("currency"),
            tax=payload.get("tax"),
            tax_rate=payload.get("tax_rate"),
            subtotal=payload.get("subtotal"),
            ocr_confidence=payload.get("ocr_confidence"),
            raw_text=payload.get("raw_text"),
            source_url=source_url,
            latency_ms=latency_ms,
            raw_response=payload,
        )

    def parse_receipt(self, *, file_bytes: Optional[bytes] = None, url: Optional[str] = None, options: Optional[Dict[str, Any]] = None) -> ReceiptExtraction:
        last_err: Optional[Exception] = None
        assert (file_bytes is not None) or (url is not None), "Provide file_bytes or url"
        for attempt in range(1, self.retries + 1):
            try:
                t0 = time.time()
                if url:
                    resp = requests.post(self.url_by_url, json={"url": url}, timeout=self.timeout)
                else:
                    files = {"file": (options.get("filename") if options else "receipt.jpg", file_bytes)}
                    resp = requests.post(self.url_file, files=files, timeout=self.timeout)
                latency_ms = int((time.time() - t0) * 1000)
                request_id = resp.headers.get("x-request-id") or resp.headers.get("X-Request-ID")
                logger.info("PaddleOCRHTTPAdapter status=%s latency_ms=%s req_id=%s", resp.status_code, latency_ms, request_id)
                resp.raise_for_status()
                payload = resp.json()
                if not payload.get("success", True):
                    raise RuntimeError(f"Paddle service reported failure: {payload}")
                return self._map(payload, source_url=url, latency_ms=latency_ms)
            except Exception as e:
                last_err = e
                logger.warning("PaddleOCR attempt %s/%s failed: %s", attempt, self.retries, e)
        raise RuntimeError(f"PaddleOCRHTTPAdapter failed after {self.retries} retries: {last_err}")


