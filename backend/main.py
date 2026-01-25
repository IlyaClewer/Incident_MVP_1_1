import json
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException, Path as FastAPIPath, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="Incident MVP")

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

PATIENTS_PATH = DATA_DIR / "patients_final.json"
DIAGNOSES_PATH = DATA_DIR / "diagnoses.json"
EXPERT_GROUPS_PATH = DATA_DIR / "expert_groups_min.json"

STATIC_DIR = BASE_DIR / "static"
INDEX_HTML = STATIC_DIR / "index.html"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # на прод лучше сузить
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache
def load_patients() -> dict:
    data = _read_json(PATIENTS_PATH)
    return data if isinstance(data, dict) else {"patients": []}


@lru_cache
def load_diagnoses() -> dict:
    data = _read_json(DIAGNOSES_PATH)
    return data if isinstance(data, dict) else {"diagnoses": []}


@lru_cache
def load_expert_groups() -> dict:
    data = _read_json(EXPERT_GROUPS_PATH)
    return data if isinstance(data, dict) else {"expert_groups": []}


def build_stac_card_diagnosis_index(diagnoses_payload: dict) -> dict[int, list[str]]:
    """
    { stac_card_id: [diagnosis_id, ...] }
    """
    index: dict[int, list[str]] = {}
    for dx in diagnoses_payload.get("diagnoses", []) or []:
        dx_id = dx.get("id")
        if not dx_id:
            continue
        for stac_id in dx.get("stac_card_ids", []) or []:
            try:
                stac_id_int = int(stac_id)
            except (TypeError, ValueError):
                continue
            index.setdefault(stac_id_int, []).append(dx_id)
    return index


# ---------- API ----------
@app.get("/api/patients")
async def api_patients():
    return load_patients()


@app.get("/api/meta")
async def api_meta():
    diagnoses = load_diagnoses()
    expert_groups = load_expert_groups()
    index = build_stac_card_diagnosis_index(diagnoses)

    return {
        "expert_groups": expert_groups.get("expert_groups", []),
        "diagnoses": diagnoses.get("diagnoses", []),
        "stac_card_diagnosis_index": index,
    }


@app.get("/api/stac-card/{stac_id}")
async def api_stac_card(stac_id: int = FastAPIPath(...)):
    data = load_patients()
    diagnoses = load_diagnoses()
    index = build_stac_card_diagnosis_index(diagnoses)

    for patient in data.get("patients", []):
        for card in patient.get("stac_cards", []):
            if str(card.get("id")) == str(stac_id):
                return {
                    "patient": patient,
                    "stac_card": card,
                    "events": card.get("events", []),
                    "diagnosis_ids": index.get(int(stac_id), []),
                }

    return {"error": "not_found"}


# ---------- Frontend (Vite dist) ----------
app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

@app.get("/", include_in_schema=False)
async def home():
    return FileResponse(INDEX_HTML)

@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(request: Request, full_path: str):
    if request.url.path.startswith("/api/"):
        raise HTTPException(status_code=404)
    candidate = STATIC_DIR / full_path
    if candidate.is_file():
        return FileResponse(candidate)
    return FileResponse(INDEX_HTML)
