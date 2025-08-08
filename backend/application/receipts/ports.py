"""
Ports (interfaces) and DTOs for OCR and Storage providers.
These live in the application layer to keep infra adapters swappable.
"""

from __future__ import annotations

from typing import Optional, Protocol, Union, Dict, Any
from pydantic import BaseModel, Field


class StoredAsset(BaseModel):
    public_id: Optional[str] = None
    secure_url: str
    width: Optional[int] = None
    height: Optional[int] = None
    bytes: Optional[int] = None
    format: Optional[str] = None


class ReceiptExtraction(BaseModel):
    engine: str = Field(..., description="paddle | openai | fallback")
    merchant: Optional[str] = None
    date: Optional[str] = Field(None, description="YYYY-MM-DD")
    total: Optional[float] = None
    currency: Optional[str] = None
    tax: Optional[float] = None
    tax_rate: Optional[float] = None
    subtotal: Optional[float] = None
    ocr_confidence: Optional[float] = None
    raw_text: Optional[str] = None
    source_url: Optional[str] = None
    latency_ms: Optional[int] = None
    raw_response: Optional[Dict[str, Any]] = None


class StorageProvider(Protocol):
    def upload(self, *, file_bytes: bytes, filename: str, mime: Optional[str] = None) -> StoredAsset:
        ...


class OCRProvider(Protocol):
    def parse_receipt(self, *, file_bytes: Optional[bytes] = None, url: Optional[str] = None, options: Optional[Dict[str, Any]] = None) -> ReceiptExtraction:
        ...


