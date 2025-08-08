
"""
Enhanced PaddleOCR (PP-OCRv5-friendly) service with robust total extraction.
This module is intentionally self-contained and light-weight so it can drop into
existing projects that expect `EnhancedPaddleOCRService.process_receipt_image(...)`.
"""

from __future__ import annotations

import os
import re
import time
import hashlib
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# Optional deps
try:
    import cv2  # type: ignore
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover
    cv2 = None  # type: ignore
    np = None  # type: ignore

try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover
    psutil = None  # type: ignore

try:
    # PaddleOCR is the only heavy dependency we rely on.
    from paddleocr import PaddleOCR  # type: ignore
except Exception:  # pragma: no cover
    PaddleOCR = None  # type: ignore


# ----------------------------- Utilities -----------------------------

def _sha(image_bgr: "np.ndarray") -> str:
    if image_bgr is None:
        return ""
    h = hashlib.sha256()
    h.update(image_bgr.data.tobytes())
    return h.hexdigest()[:16]


def _now() -> float:
    return time.time()


@dataclass
class ExtractedReceipt:
    merchant: Optional[str] = None
    invoice_number: Optional[str] = None
    date: Optional[str] = None  # YYYY-MM-DD
    total: Optional[float] = None
    currency: Optional[str] = None
    payment_method: Optional[str] = None
    confidence: float = 0.0
    receipt_type: Optional[str] = None  # e.g., "thermal", "a4", etc.
    needs_review: bool = False


# --------------------------- Main Service ----------------------------

class EnhancedPaddleOCRService:
    """
    Minimal service wrapper that favors PP-OCRv5 and applies safer parsing.
    Focus: extracting merchant, date, and total with fewer false-positives.
    """

    # Money patterns
    MONEY_RX = re.compile(r"[£€$]?\s*\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?p?\b", re.I)
    CURRENCY_MONEY_RX = re.compile(r"([£€$])\s*\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\b", re.I)

    # Date patterns (UK and ISO-ish)
    DATE_PATTERNS = [
        re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"),  # 16/09/22 or 16-09-2022
        re.compile(r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b"),    # 2022/09/16
        re.compile(r"\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4}\b", re.I),  # 16 Sep 2022
    ]

    # Keywords for total scoring
    TOTAL_KW_PRIORITY = {"TOTAL", "AMOUNT DUE", "AMOUNT DUE:", "BALANCE DUE", "TO PAY", "CARD", "CASH", "CHANGE DUE", "TOTAL DUE"}
    TOTAL_KW_CONTEXT = {"SUBTOTAL", "SUB-TOTAL", "DISCOUNT", "VAT", "TAX", "EPS"}
    TOTAL_KW = TOTAL_KW_PRIORITY | TOTAL_KW_CONTEXT
    SUBTOTAL_KW = {"SUBTOTAL", "SUB-TOTAL"}

    # Quick merchant dictionary (extend as needed)
    KNOWN_MERCHANTS = ["ASDA", "TESCO", "ALDI", "SAINSBURY", "MORRISONS", "LIDL", "ACE HARDWARE", "ACE", "COOP", "WALMART"]

    def __init__(self, lang: str = "en", use_gpu: Optional[bool] = None) -> None:
        self.lang = lang
        self.use_gpu = bool(use_gpu) if use_gpu is not None else False
        print(f"INFO: Initializing Enhanced PaddleOCR with PP-OCRv5 models (Lang={self.lang}, GPU={self.use_gpu})")

        if PaddleOCR is None:
            self.ocr = None
            print("WARNING: paddleocr not installed; falling back to dummy OCR.")
        else:
            # PaddleOCR downloads proper models automatically. No explicit v5 flag,
            # but defaults are compatible with PP-OCR(mobile/server) pipelines.
            # Build kwargs based on PaddleOCR's signature to avoid 'Unknown argument' errors (Windows/env variations)
            try:
                import inspect
                sig = inspect.signature(PaddleOCR.__init__)
                kwargs = {k: v for k, v in {
                    'use_angle_cls': True,
                    'lang': self.lang,
                    'use_gpu': self.use_gpu,
                    'show_log': False,
                }.items() if k in sig.parameters}
            except Exception:
                kwargs = {'use_angle_cls': True, 'lang': self.lang}
                if hasattr(PaddleOCR.__init__, '__code__') and 'use_gpu' in PaddleOCR.__init__.__code__.co_varnames:
                    kwargs['use_gpu'] = self.use_gpu
            self.ocr = PaddleOCR(**kwargs)
        print(f"INFO: Enhanced PaddleOCR ready (lang={self.lang}, gpu={self.use_gpu})")

    # --------------------- OCR & Parsing helpers ---------------------

    def _norm_digits(self, s: str) -> str:
        table = str.maketrans({
            "O": "0", "o": "0", "U": "0", "D": "0", "Q": "0",
            "S": "5", "s": "5", "I": "1", "l": "1", "B": "8", "Z": "2"
        })
        return s.translate(table)

    def _to_float(self, s: str) -> Optional[float]:
        s = self._norm_digits(s)
        s_clean = re.sub(r"[^\d.p]", "", s.lower())
        if not s_clean:
            return None
        # pence like "50p"
        if "p" in s_clean and "." not in s_clean:
            try:
                return float(s_clean.replace("p", "")) / 100.0
            except Exception:
                return None
        if "." in s_clean:
            try:
                return float(s_clean)
            except Exception:
                return None
        try:
            return float(s_clean)
        except ValueError:
            return None

    
    def _extract_text(self, image_path: str) -> Tuple[str, List[Tuple[str, float]]]:
        """
        Returns (full_text, [(line_text, confidence), ...])
        """
        if self.ocr is None:
            # Fallback: read bytes and pretend
            try:
                with open(image_path, "rb") as f:
                    data = f.read()
                fake = f"FAKE_OCR_{len(data)}"
                return fake, [(fake, 0.0)]
            except Exception:
                return "", []

        # Some PaddleOCR builds on Windows don't accept 'cls' or other kwargs.
        # Try the safest call first, then progressively add flags only if needed.
        result = None
        errors = []
        for kwargs in ({}, {'det': True, 'rec': True}, {'cls': True}, {'det': True, 'rec': True, 'cls': True}):
            try:
                result = self.ocr.ocr(image_path, **{k:v for k,v in kwargs.items()
                                                     if k in getattr(self.ocr.ocr, '__code__', type('x',(object,),{'co_varnames':()})()).co_varnames})
                break
            except TypeError as e:
                errors.append(str(e))
                continue
            except Exception as e:
                errors.append(str(e))
                continue

        if result is None:
            raise RuntimeError("PaddleOCR.ocr failed: " + " | ".join(errors))

        lines: List[Tuple[str, float]] = []
        for page in result:
            for line in page:
                txt = line[1][0] if isinstance(line, list) else ""
                conf = float(line[1][1]) if isinstance(line, list) else 0.0
                if txt:
                    lines.append((txt.strip(), conf))
        full_text = "\n".join(t for t, _ in lines)
        return full_text, lines
    def _extract_date(self, full: str) -> Optional[str]:
        from datetime import datetime
        for pattern in self.DATE_PATTERNS:
            m = pattern.search(full)
            if not m:
                continue
            raw = m.group()
            # Try common UK/ISO
            candidates = [
                ("%d/%m/%Y", raw.replace("-", "/")),
                ("%d/%m/%y", raw.replace("-", "/")),
                ("%Y/%m/%d", raw.replace("-", "/")),
                ("%d %b %Y", raw),
                ("%d %B %Y", raw),
            ]
            for fmt, s in candidates:
                try:
                    return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
                except ValueError:
                    pass
        return None

    def _guess_currency(self, text: str) -> Optional[str]:
        if "£" in text:
            return "GBP"
        if "$" in text:
            return "USD"
        if "€" in text:
            return "EUR"
        return None

    def _find_merchant(self, lines: List[str]) -> Optional[str]:
        # Take the first block of up to 5 upper-ish lines, check against dictionary
        for s in lines[:8]:
            s_up = re.sub(r"[^A-Z ]", "", s.upper()).strip()
            for m in self.KNOWN_MERCHANTS:
                if m in s_up:
                    return m
        # fallback: the first upper line
        for s in lines[:5]:
            s_up = re.sub(r"[^A-Z &]", "", s.upper()).strip()
            if len(s_up) >= 3:
                return s_up[:40]
        return None

    def _find_total(self, lines: List[str]) -> Optional[float]:
        """Enhanced logic to find the total amount (PP-OCRv5 friendly)."""
        amounts: List[Tuple[float, str, int, bool]] = []  # (value, line_text, line_index, has_currency)

        for i, line in enumerate(lines):
            line_norm = self._norm_digits(line)
            has_currency = bool(self.CURRENCY_MONEY_RX.search(line_norm)) or any(sym in line_norm for sym in ('£','€','$'))
            for m in self.MONEY_RX.finditer(line_norm):
                val = self._to_float(m.group())
                if val is not None:
                    amounts.append((val, line, i, has_currency))

        if not amounts:
            return None

        def score(value: float, text: str, idx: int, has_currency: bool) -> tuple:
            up = text.upper()
            kw = 0
            if any(k in up for k in self.TOTAL_KW_PRIORITY):
                kw += 3
            if any(k in up for k in self.TOTAL_KW_CONTEXT):
                kw += 1
            if has_currency:
                kw += 2
            return (kw, idx, value)

        tail_start = max(0, len(lines) - 10)
        tail = [a for a in amounts if a[2] >= tail_start]
        if tail:
            best = max(tail, key=lambda a: score(*a))
            if score(*best)[0] >= 2:
                return best[0]

        curr = [a for a in amounts if a[3]]
        if curr:
            curr.sort(key=lambda a: (a[2], a[0]))
            for cand in reversed(curr):
                if any(k in cand[1].upper() for k in self.TOTAL_KW_PRIORITY):
                    return cand[0]
            return curr[-1][0]

        safe = [a for a in amounts if not any(k in a[1].upper() for k in (['VAT','TAX'] + list(self.SUBTOTAL_KW)))]
        if safe:
            return max(safe, key=lambda a: a[0])[0]

        return max(amounts, key=lambda a: a[0])[0]

    def _vat_details(self, text: str) -> Optional[str]:
        # Simple VAT presence indicator
        if re.search(r"\bVAT\b|\bTAX\b", text, re.I):
            return "VAT/TAX detected"
        return None

    # ------------------------- Public API ----------------------------

    def process_receipt_image(self, image_path: str) -> Dict[str, Any]:
        """
        High-level pipeline that returns a dict consumable by the tester.
        NOTE: We intentionally DO NOT include 'category' to remain compatible
        with older OCRData(**payload) callers.
        """
        start = _now()

        if cv2 is None or np is None:
            return {
                "success": False,
                "message": "OpenCV / NumPy not available",
                "processing_time": 0.0,
            }

        img = cv2.imread(image_path)
        if img is None:
            return {"success": False, "message": "Image not found", "processing_time": 0.0}

        full_text, lines_with_conf = self._extract_text(image_path)
        lines = [t for t, _ in lines_with_conf]
        avg_conf = round(sum(c for _, c in lines_with_conf) / max(1, len(lines_with_conf)) * 100.0, 1) if lines_with_conf else 0.0

        rec = ExtractedReceipt()
        rec.currency = self._guess_currency(full_text)
        rec.date = self._extract_date(full_text)
        rec.total = self._find_total(lines)
        rec.merchant = self._find_merchant(lines)
        rec.payment_method = "CARD" if re.search(r"\bCARD\b|MASTERCARD|VISA|CONTACTLESS", full_text, re.I) else None
        rec.receipt_type = "thermal" if img.shape[1] <= 900 and img.shape[0] > img.shape[1] else "a4"
        rec.confidence = avg_conf
        rec.needs_review = rec.total is None or rec.merchant is None

        dt = _now() - start

        payload = {
            "success": bool(rec.total),
            "message": "OCR processing completed successfully" if rec.total else "Unable to extract total",
            "processing_time": round(dt, 3),
            "ocr_confidence": round(avg_conf, 1),
            "field_confidence": {
                "merchant": 0.9 if rec.merchant else 0.0,
                "total": 0.9 if rec.total else 0.0,
                "date": 0.7 if rec.date else 0.0,
            },
            "needs_review": rec.needs_review,

            # flattened receipt fields
            "merchant": rec.merchant,
            "invoice_number": rec.invoice_number,
            "date": rec.date,
            "total": rec.total,
            "currency": rec.currency,
            "payment_method": rec.payment_method,
            "is_thermal": rec.receipt_type == "thermal",
            "layout_type": rec.receipt_type,
            "vat_info": self._vat_details(full_text),

            # tracing
            "raw_text": full_text,
            "image_hash": _sha(img),
            "image_dimensions": f"{img.shape[1]}x{img.shape[0]}",
            "rss_mb": psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024) if psutil else 0,
        }
        # DO NOT include 'category' to avoid legacy OCRData(**payload) errors
        return payload
