"""MedVerify API (FastAPI). Reference DB is bundled read-only; history lives in /tmp (ephemeral)."""
import os, re, sqlite3, sys
from contextlib import closing
from datetime import date, datetime
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Query
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.verification import select_official_matches  # existing matching rules

app = FastAPI(title="MedVerify API")
DB = Path(__file__).resolve().parent.parent / "data" / "medicine_reference.db"
HIST = "/tmp/medverify_history.db"

def ref():
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True); c.row_factory = sqlite3.Row; return c

def hist():
    c = sqlite3.connect(HIST); c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS history(id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT,
        brand TEXT, batch TEXT, score INT, level TEXT, outcome TEXT)""")
    return c

def clean(v): return re.sub(r"\s+", " ", str(v or "")).strip()

class VerifyIn(BaseModel):
    brand: str
    ingredient: str = ""
    dosage_form: str = ""
    batch: str = ""
    product_code: str = ""
    manufacturer: str = ""
    mfg_date: Optional[str] = None
    expiry_date: Optional[str] = None
    mrp: Optional[float] = None

def pdate(s):
    try: return datetime.strptime(s, "%Y-%m-%d").date() if s else None
    except ValueError: return None

@app.post("/api/verify")
def verify(p: VerifyIn):
    with closing(ref()) as c: rows = [dict(r) for r in c.execute("SELECT * FROM medicine_reference")]
    name = " ".join(x for x in [p.brand, p.ingredient] if x)
    matches, kind = select_official_matches(rows, p.brand or p.ingredient, p.product_code)
    f = []  # findings: (check, status ok|warn|bad|info, detail, risk points)
    msg = {"name_only": ("ok", "Reference listing found for this name.", 0),
           "name_and_code": ("ok", "Name and product code match the same reference listing.", 0),
           "code_mismatch": ("bad", "Name found, but the entered product code is not in the reference listing.", 30),
           "code_name_mismatch": ("bad", "Product code belongs to a different medicine name.", 35),
           "no_match": ("warn", "No reference match. This does not prove the medicine is fake; the database is limited.", 35)}[kind]
    f.append(("Identity match", *msg))
    if matches and p.manufacturer:
        ok = any(clean(p.manufacturer).casefold() in clean(m["labeler_name"]).casefold() or
                 clean(m["labeler_name"]).casefold() in clean(p.manufacturer).casefold() for m in matches)
        f.append(("Manufacturer", "ok" if ok else "warn",
                  "Manufacturer matches a reference labeler." if ok else "Manufacturer differs from the reference labeler(s).", 0 if ok else 15))
    if matches and p.dosage_form:
        ok = any(clean(p.dosage_form).casefold() in clean(m["dosage_form"]).casefold() for m in matches)
        f.append(("Dosage form", "ok" if ok else "warn", "Dosage form matches." if ok else "Dosage form differs from the reference listing.", 0 if ok else 8))
    f.append(("Batch lookup", "info" if p.batch else "warn",
              "Batch recorded, but no public batch-verification source exists, so it was not authenticated." if p.batch else "No batch number entered.", 0 if p.batch else 10))
    m, e, today = pdate(p.mfg_date), pdate(p.expiry_date), date.today()
    if e is None: f.append(("Expiry date", "warn", "No valid expiry date entered.", 10))
    elif e < today: f.append(("Expiry date", "bad", f"Expired on {e}.", 40))
    elif (e - today).days <= 30: f.append(("Expiry date", "warn", f"Expires within 30 days ({e}).", 10))
    else: f.append(("Expiry date", "ok", f"Valid until {e}.", 0))
    if m and e and m >= e: f.append(("Date order", "bad", "Manufacturing date is on or after the expiry date.", 30))
    elif m and m > today: f.append(("Date order", "bad", "Manufacturing date is in the future.", 30))
    if p.mrp is not None:
        bad = p.mrp <= 0 or p.mrp > 100000
        f.append(("MRP sanity", "warn" if bad else "info",
                  "MRP is outside a plausible range." if bad else "MRP recorded. No price reference data is loaded, so price anomalies are not assessed.", 10 if bad else 0))
    f.append(("Recall check", "info", "Not performed: no recall dataset (e.g. CDSCO alerts) is connected. Check the CDSCO website manually.", 0))
    score = min(100, sum(x[3] for x in f))
    level = "low" if score < 25 else "medium" if score < 55 else "high"
    outcome = {"low": "No obvious issue found", "medium": "Needs checking", "high": "Suspicious"}[level]
    with closing(hist()) as h:
        h.execute("INSERT INTO history(at,brand,batch,score,level,outcome) VALUES(?,?,?,?,?,?)",
                  (datetime.utcnow().isoformat(timespec="seconds"), p.brand or p.ingredient, p.batch, score, level, outcome)); h.commit()
    return {"score": score, "level": level, "outcome": outcome, "match_type": kind,
            "findings": [{"check": a, "status": b, "detail": c_} for a, b, c_, _ in f],
            "references": [{k: m_[k] for k in ("brand_name", "labeler_name", "product_ndc", "strength", "source_type")} for m_ in matches[:5]],
            "limitations": "This screens label details against product-level listings. It cannot prove a physical pack is genuine. Confirm with a pharmacist or the manufacturer."}

@app.get("/api/medicines")
def medicines(q: str = "", source: str = "", page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    where, args = [], []
    if q:
        where.append("(brand_name LIKE ? OR generic_name LIKE ? OR active_ingredients LIKE ? OR labeler_name LIKE ?)"); args += [f"%{q}%"] * 4
    if source in ("demo", "openfda"): where.append("source_type = ?"); args.append(source)
    w = (" WHERE " + " AND ".join(where)) if where else ""
    with closing(ref()) as c:
        total = c.execute(f"SELECT COUNT(*) FROM medicine_reference{w}", args).fetchone()[0]
        off = (page - 1) * page_size
        rows = [dict(r) for r in c.execute(f"SELECT brand_name,generic_name,strength,dosage_form,labeler_name,product_ndc,source_type FROM medicine_reference{w} ORDER BY brand_name LIMIT ? OFFSET ?", args + [page_size, off])]
    return {"total": total, "page": page, "page_size": page_size, "offset": off, "items": rows}

@app.get("/api/stats")
def stats():
    with closing(ref()) as c:
        by = dict(c.execute("SELECT source_type, COUNT(*) FROM medicine_reference GROUP BY 1").fetchall())
    with closing(hist()) as h:
        scans = h.execute("SELECT COUNT(*) FROM history").fetchone()[0]
        flagged = h.execute("SELECT COUNT(*) FROM history WHERE level!='low'").fetchone()[0]
    return {"total_records": sum(by.values()), "by_source": by, "scans": scans, "flagged": flagged}

@app.get("/api/history")
def history(limit: int = Query(50, ge=1, le=200)):
    with closing(hist()) as h:
        return {"items": [dict(r) for r in h.execute("SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,))],
                "note": "History is stored in temporary serverless storage and may reset."}

# Local run only (python -m uvicorn api.index:app): Vercel serves public/ itself.
if not os.environ.get("VERCEL"):
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=str(Path(__file__).resolve().parent.parent / "public"), html=True), name="site")
