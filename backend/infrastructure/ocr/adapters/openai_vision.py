"""
OpenAI Vision adapter that produces a normalized ReceiptExtraction.
If provided bytes, it uploads to Cloudinary first via StorageProvider.
"""

from __future__ import annotations

import json
import os
import time
import logging
from typing import Optional, Dict, Any

from django.conf import settings
from pydantic import BaseModel

from application.receipts.ports import OCRProvider, ReceiptExtraction, StorageProvider

logger = logging.getLogger(__name__)


class OpenAIVisionAdapter(OCRProvider):
    def __init__(self, storage: StorageProvider):
        api_key = os.getenv("OPENAI_API_KEY", getattr(settings, "OPENAI_API_KEY", None))
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        from openai import OpenAI  # lazy import
        self.client = OpenAI(api_key=api_key)
        self.storage = storage

    def _build_prompt(self) -> str:
        return (
            "Extract structured fields from the receipt image. Return strict JSON with keys: "
            "merchant, date (YYYY-MM-DD), currency (GBP/EUR/USD if inferable), subtotal (number), "
            "tax (number), tax_rate (number or null), total (number), ocr_confidence (0-100), raw_text (string)."
        )

    def _call_model(self, image_url: str) -> Dict[str, Any]:
        # Use responses with JSON mode when available
        try:
            t0 = time.time()
            resp = self.client.chat.completions.create(
                model=getattr(settings, "OPENAI_VISION_MODEL", "gpt-4o-mini"),
                temperature=0.1,
                messages=[
                    {
                        "role": "system",
                        "content": self._build_prompt(),
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Parse this receipt."},
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url},
                            },
                        ],
                    },
                ],
                response_format={"type": "json_object"},
            )
            latency_ms = int((time.time() - t0) * 1000)
            content = resp.choices[0].message.content or "{}"
            data = json.loads(content)
            data["_latency_ms"] = latency_ms
            return data
        except Exception as e:
            logger.error("OpenAI Vision call failed: %s", e)
            raise

    def parse_receipt(self, *, file_bytes: Optional[bytes] = None, url: Optional[str] = None, options: Optional[Dict[str, Any]] = None) -> ReceiptExtraction:
        if not url and not file_bytes:
            raise ValueError("Provide either file_bytes or url")

        source_url: Optional[str] = url
        # Upload if bytes
        if file_bytes is not None and not source_url:
            filename = (options or {}).get("filename", "receipt.jpg")
            asset = self.storage.upload(file_bytes=file_bytes, filename=filename, mime=(options or {}).get("mime"))
            source_url = asset.secure_url

        raw = self._call_model(source_url)
        latency_ms = int(raw.pop("_latency_ms", 0))

        return ReceiptExtraction(
            engine="openai",
            merchant=raw.get("merchant"),
            date=raw.get("date"),
            total=raw.get("total"),
            currency=raw.get("currency") or "GBP",
            tax=raw.get("tax"),
            tax_rate=raw.get("tax_rate"),
            subtotal=raw.get("subtotal"),
            ocr_confidence=raw.get("ocr_confidence"),
            raw_text=raw.get("raw_text"),
            source_url=source_url,
            latency_ms=latency_ms,
            raw_response=raw,
        )


