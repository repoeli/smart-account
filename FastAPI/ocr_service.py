from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from paddleocr import PaddleOCR
from typing import List, Optional, Tuple
import tempfile, os, re

# -----------------------------
# App & OCR engine (no thermal tricks)
# -----------------------------
app = FastAPI()
ocr = PaddleOCR(use_angle_cls=True, lang="en")  # PP-OCRv4 (English), CPU

# -----------------------------
# Regex & constants
# -----------------------------
# Prefer decimals / pence; use lookarounds to avoid matching inside long IDs
DECIMAL_MONEY_RX = re.compile(r"(?<!\d)(?:[£€$]\s*)?\d{1,3}(?:,\d{3})*\.\d{1,2}(?!\d)", re.I)
PENNIES_RX       = re.compile(r"(?<!\d)(?:[£€$]\s*)?\d{1,3}(?:,\d{3})*p(?![a-zA-Z0-9])", re.I)
INTEGER_MONEY_RX = re.compile(r"(?<!\d)(?:[£€$]\s*)?\d{1,3}(?:,\d{3})*(?![\dp])", re.I)

DATE_RX = [
    re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"),
    re.compile(r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b"),
    re.compile(r"\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4}\b", re.I),
    re.compile(r"\b\d{1,2}\.\d{1,2}\.\d{2,4}\b"),  # dd.mm.yy
]

TIME_LINE_RX = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")
ID_TOKEN_RX  = re.compile(r"\b(IC#|EPS ?NO|SEQ|TR\.|ST\.|OP\.|AID|TERMINAL|AUTH|TEL|PHONE|TRAN ID|MERCHANT ID)\b", re.I)

TOTAL_ANCHORS = {"TOTAL","AMOUNT DUE","TOTAL DUE","TO PAY","BALANCE DUE","AMOUNT"}
BAD_TOTAL_TERMS = {
    "TOTAL TAX","TOTAL NUMBER","TOTAL NO","TOTAL ITEMS","TOTAL ITEM","TOTAL QTY",
    "TOTAL SAVINGS","TOTAL SAVING","TOTAL DISCOUNT","TOTAL POINTS","TOTAL REWARDS",
    "SUBTOTAL","SUB-TOTAL"
}
PAYMENT_KW = {"CARD","CASH","PAID","MASTERCARD","VISA","AMEX","DEBIT","CREDIT","AMOUNT"}
TAX_KW = {"TAX","VAT","SALES TAX","GST","HST","TVA"}

UK_MERCHANTS = {"ASDA","TESCO","SAINSBURY","SAINSBURY'S","MORRISONS","LIDL","ALDI","COOP","WAITROSE"}
MERCHANT_STOP_PHRASES = {
    "PLEASE KEEP THIS COPY FOR YOUR RECORDS","PLEASE KEEP THIS COPY",
    "THANK YOU","THANK YOU!","PLEASE COME AGAIN","PHOTO SHARING",
    "SHOP ONLINE","HOME DELIVERY","RECEIPT","SUMMARY"
}

# -----------------------------
# Helpers
# -----------------------------
def norm_digits(s: str) -> str:
    return s.translate(str.maketrans({
        'O':'0','o':'0','Q':'0','U':'0',
        'S':'5','s':'5','I':'1','l':'1','B':'8','Z':'2'
    }))

def to_float(s: str) -> Optional[float]:
    s = norm_digits(s)
    s_clean = re.sub(r"[^\d.p]", "", s.lower())
    if not s_clean:
        return None
    if "p" in s_clean and "." not in s_clean:  # 50p -> 0.50
        try: return float(s_clean.replace("p",""))/100.0
        except: return None
    try: return float(s_clean)
    except: return None

def _amounts_in_text(t: str) -> List[float]:
    # skip typical non-price lines
    if TIME_LINE_RX.search(t) or ID_TOKEN_RX.search(t):
        return []
    hits = list(DECIMAL_MONEY_RX.finditer(t)) + list(PENNIES_RX.finditer(t))
    if hits:
        vals = []
        for m in hits:
            v = to_float(m.group())
            if v is not None: vals.append(v)
        return vals
    # integers fallback (avoid bare 1..9 as qty)
    vals = []
    for m in INTEGER_MONEY_RX.finditer(t):
        raw = m.group()
        if ("£" not in raw and "€" not in raw and "$" not in raw) and not re.search(r"\d+\.\d+", raw):
            try:
                if int(re.sub(r"[^\d]", "", raw)) < 10:  # looks like qty
                    continue
            except: pass
        v = to_float(raw)
        if v is not None: vals.append(v)
    return vals

def extract_date(full: str) -> Optional[str]:
    from datetime import datetime
    for rx in DATE_RX:
        for m in rx.finditer(full):
            raw = m.group()
            s = raw.replace("-", "/").replace(".", "/")
            for fmt in ("%d/%m/%Y","%d/%m/%y","%Y/%m/%d","%d %b %Y","%d %B %Y","%m/%d/%Y","%m/%d/%y"):
                try: return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
                except: pass
    return None

def guess_currency(text: str, merchant: Optional[str]=None) -> Optional[str]:
    if "£" in text: return "GBP"
    if "€" in text: return "EUR"
    if "$" in text: return "USD"
    if merchant and merchant.upper() in UK_MERCHANTS: return "GBP"
    return None

def find_merchant(lines: List[str]) -> Optional[str]:
    known = [
        "ASDA","TESCO","ALDI","SAINSBURY","SAINSBURY'S","MORRISONS",
        "LIDL","COSTCO","COSTCO WHOLESALE","WAITROSE","ACE HARDWARE","WALMART","NANNY BILLS","NANNY BILL'S"
    ]
    for s in lines[:30]:
        up = re.sub(r"[^A-Z '&]", "", s.upper()).strip()
        for m in known:
            if m in up:
                return m
    for s in lines[:15]:
        if ID_TOKEN_RX.search(s): 
            continue
        up = re.sub(r"[^A-Z '&]", "", s.upper()).strip()
        if len(up) >= 3 and up not in MERCHANT_STOP_PHRASES:
            bad = {"TOTAL","CASH","CHANGE","SUBTOTAL","TAX","VAT","RECEIPT","SUMMARY"}
            if not any(b in up for b in bad):
                if len(up) >= 6 or " " in up:
                    return up[:40]
    return None

def _is_bad_total_line(up: str) -> bool:
    return any(b in up for b in BAD_TOTAL_TERMS)

def find_total(lines: List[str]) -> Optional[float]:
    # 1) explicit anchors (bottom-up), prefer decimals, then max value
    for idx in range(len(lines)-1, -1, -1):
        up = lines[idx].upper()
        if any(k in up for k in TOTAL_ANCHORS) and not _is_bad_total_line(up):
            here = [v for v in _amounts_in_text(lines[idx]) if 0 < v <= 5000]
            if here:
                decs = [v for v in here if abs(v - int(v)) > 1e-9]
                return (decs[-1] if decs else max(here))
            # neighbors
            cand = []
            for j in (idx+1, idx+2, idx-1):
                if 0 <= j < len(lines):
                    for v in _amounts_in_text(lines[j]):
                        if 0 < v <= 5000:
                            cand.append(v)
            if cand:
                decs = [v for v in cand if abs(v - int(v)) > 1e-9]
                return (decs[-1] if decs else max(cand))

    # 2) payment section near bottom
    for idx in range(len(lines)-1, -1, -1):
        up = lines[idx].upper()
        if any(k in up for k in PAYMENT_KW) or "APPROVED" in up:
            cand = []
            for j in range(max(0, idx-4), min(len(lines), idx+5)):
                for v in _amounts_in_text(lines[j]):
                    if 0 < v <= 5000:
                        cand.append(v)
            if cand:
                decs = [v for v in cand if abs(v - int(v)) > 1e-9]
                return (decs[-1] if decs else max(cand))

    # 3) global fallback: prefer decimals, otherwise largest plausible
    amounts = []
    for i, line in enumerate(lines):
        if any(k in line.upper() for k in ("ITEMS SOLD","INSTANT SAVINGS")):
            continue
        for v in _amounts_in_text(line):
            if 0 < v <= 5000:
                amounts.append(v)
    if not amounts:
        return None
    decs = [v for v in amounts if abs(v - int(v)) > 1e-9]
    return (max(decs) if decs else max(amounts))

def _parse_tax_rate(text: str) -> Optional[float]:
    m = re.search(r'(\d{1,2}(?:\.\d{1,2})?)\s*%', text)
    if m:
        try: return float(m.group(1))
        except: return None
    return None

def find_tax(lines: List[str], total: Optional[float]=None) -> Tuple[Optional[float], Optional[float], str]:
    def ok(v: float) -> bool:
        if v <= 0: return False
        if total is not None and v > total * 0.35:  # cap to avoid “20” on 20.16
            return False
        return v <= 5000
    cands: List[Tuple[int,float,str]] = []
    for i in range(len(lines)-1, -1, -1):
        up = lines[i].upper()
        if any(k in up for k in TAX_KW) or "TOTAL TAX" in up:
            for v in _amounts_in_text(lines[i]):
                if ok(v):
                    cands.append((i, v, up))
            for j in (i+1, i-1):
                if 0 <= j < len(lines):
                    for v in _amounts_in_text(lines[j]):
                        if ok(v):
                            cands.append((j, v, lines[j].upper()))
    if cands:
        cands.sort(key=lambda t: (("TAX" in t[2] or "VAT" in t[2]), abs(t[1]-int(t[1]))>1e-9, 0.0005*t[0]), reverse=True)
        best = cands[0]
        rate = _parse_tax_rate("\n".join(x[2] for x in cands)) or _parse_tax_rate(best[2])
        return (best[1], rate, "anchor")
    return (None, None, "none")

def find_subtotal(lines: List[str], total: Optional[float], tax: Optional[float]) -> Tuple[Optional[float], str]:
    for i in range(len(lines)-1, -1, -1):
        up = lines[i].upper()
        if "SUBTOTAL" in up or "SUB-TOTAL" in up:
            vals = [v for v in _amounts_in_text(lines[i]) if v > 0 and (total is None or v <= total)]
            if not vals and i+1 < len(lines):
                vals = [v for v in _amounts_in_text(lines[i+1]) if v > 0 and (total is None or v <= total)]
            if vals:
                decs = [v for v in vals if abs(v - int(v)) > 1e-9]
                return ((decs[-1] if decs else max(vals)), "anchor")
    if total is not None and tax is not None:
        st = round(total - tax, 2)
        if 0 < st <= total + 1e-6:
            return (st, "computed")
    return (None, "none")

# -----------------------------
# Routes
# -----------------------------
@app.get("/health")
def health():
    return {"ok": True}

@app.post("/ocr/receipt")
async def ocr_receipt(file: UploadFile = File(...)):
    data = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(data); tmp.flush()
        path = tmp.name
    try:
        result = ocr.ocr(path)  # single pass, no preprocessing
        lines = [t[0] for page in result for _, t in page]
        confs = [float(t[1]) for page in result for _, t in page]
        full = "\n".join(lines)

        merchant = find_merchant(lines)
        total = find_total(lines)
        tax, tax_rate, _ = find_tax(lines, total)
        subtotal, subtotal_source = find_subtotal(lines, total, tax)

        if tax is None and subtotal is not None and total is not None:
            tax = round(max(0.0, total - subtotal), 2)
            if tax_rate is None and subtotal > 0:
                tax_rate = round(100.0 * tax / subtotal, 2)

        payload = {
            "success": total is not None,
            "merchant": merchant,
            "date": extract_date(full),
            "total": total,
            "currency": guess_currency(full, merchant),
            "tax": tax,
            "tax_rate": tax_rate,
            "subtotal": subtotal,
            "subtotal_source": subtotal_source,
            "ocr_confidence": round((sum(confs)/len(confs))*100,1) if confs else 0.0,
            "raw_text": full,
        }
        if not payload["success"]:
            payload["message"] = "Unable to extract total"
        return JSONResponse(payload)
    finally:
        try: os.remove(path)
        except: pass

@app.post("/ocr/receipt-by-url")
async def ocr_receipt_by_url(payload: dict):
    import urllib.request
    url = payload.get("url")
    if not url:
        return JSONResponse({"success": False, "error": "url required"}, status_code=400)
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            data = r.read()
        class _F:
            async def read(self_inner): return data
        return await ocr_receipt(file=_F())
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
