from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any

from app.services.medwood_station_pipeline import (
    process_station_json,
    process_station_excel
)

router = APIRouter(
    prefix="/fdif/medwood/stations",
    tags=["Medwood - Stations"]
)


# -----------------------------
# JSON INGESTION
# -----------------------------
@router.post("")
def ingest_station(body: Dict[str, Any]):
    try:
        return process_station_json(body)
    except Exception as e:
        raise HTTPException(400, str(e))


# -----------------------------
# EXCEL UPLOAD
# -----------------------------
@router.post("/upload")
async def upload_stations(file: UploadFile = File(...)):
    try:
        return process_station_excel(file)
    except Exception as e:
        raise HTTPException(400, str(e))
