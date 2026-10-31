# Counterfeit Medicine System (MedVerify)

A web application for reviewing medicine label details against a public product-reference catalogue. The backend is FastAPI (`api/index.py`) and the frontend is one HTML page with Tailwind CSS and vanilla JavaScript (`public/index.html`). It deploys on Vercel and runs locally. The app has six sections: Home, Verify Medicine, result view, Database Explorer, Analytics and History, and About and Safety.

## Run locally (Windows)
Double-click `run_windows.bat`, then open http://localhost:8000. The first setup needs internet access. Or run manually:
```
python -m pip install -r requirements.txt uvicorn requests pytest
python -m uvicorn api.index:app --port 8000
```

## Deploy on Vercel
1. `git init`, `git add .`, `git commit -m "MedVerify"`, then push to a new GitHub repository.
2. In Vercel choose Add New, Project, import the repository, keep Framework Preset as **Other**, and click Deploy.
3. Check `https://<your-app>.vercel.app/api/stats` returns JSON.

`data/medicine_reference.db` must stay committed to Git: Vercel reads it as a read-only file. Scan history is stored in temporary `/tmp` storage and resets when the function restarts.

## API
- `POST /api/verify`: screens label details and returns a 0-100 risk score with findings.
- `GET /api/medicines?q=&source=&page=&page_size=`: paginated, searchable reference records.
- `GET /api/stats`: record counts, scans and flagged results.
- `GET /api/history`: recent verification log.

## Project structure
- `api/index.py`: FastAPI app (top-level `app`), endpoints and scoring.
- `public/index.html`: the whole user interface.
- `src/verification.py`: name and product-code matching rules.
- `src/data_store.py`: SQLite database helpers and demo-row loader.
- `src/reference_sync.py`: downloads openFDA NDC Directory listings.
- `scripts/sync_reference_database.py`: terminal command to refresh 500 records, then commit the updated database.
- `data/`: `medicine_reference.db` (500 openFDA listings plus 12 fictional demo rows) and `demo_medicines.csv`.
- `tests/`: pytest tests for matching, storage and sync. Run `python -m pytest`.
- `vercel.json`, `requirements.txt`: deployment configuration.

## Data sources
Real data: openFDA NDC Directory API (US FDA). Demo data: 12 fictional rows made for this project. CDSCO pages are linked only; no CDSCO data is imported.

## Limitations
- openFDA data is US-focused, not an Indian approval database.
- A listing match cannot prove a physical pack is genuine; no match does not mean a medicine is fake.
- Batch numbers are not verified with manufacturers, and no recall dataset is connected.
- Price checks only flag impossible MRP values.
- Next steps: an Indian data source, batch-authentication API, QR/barcode scanning, persistent history database, privacy review.
