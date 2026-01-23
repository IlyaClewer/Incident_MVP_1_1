import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Path as FastAPIPath, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="Incident MVP")

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "patients_final.json"
STATIC_DIR = BASE_DIR / "static"
INDEX_HTML = STATIC_DIR / "index.html"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # на прод лучше сузить
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_data():
    if not DATA_PATH.exists():
        return {"patients": []}
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))

# ---------- API ----------
@app.get("/api/patients")
async def api_patients():
    return load_data()

@app.get("/api/stac-card/{stac_id}")
async def api_stac_card(stac_id: int = FastAPIPath(...)):
    data = load_data()
    for patient in data.get("patients", []):
        for card in patient.get("stac_cards", []):
            if str(card.get("id")) == str(stac_id):
                return {"patient": patient, "stac_card": card, "events": card.get("events", [])}
    return {"error": "not_found"}

# ---------- Frontend (Vite dist) ----------
# Vite по умолчанию грузит ассеты как /assets/...
app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")  # [web:406][web:430]

@app.get("/", include_in_schema=False)
async def home():
    return FileResponse(INDEX_HTML)

# SPA fallback (если используешь history-роутинг; для hash-роутинга не мешает)
@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(request: Request, full_path: str):
    if request.url.path.startswith("/api/"):
        raise HTTPException(status_code=404)
    candidate = STATIC_DIR / full_path
    if candidate.is_file():
        return FileResponse(candidate)
    return FileResponse(INDEX_HTML)
