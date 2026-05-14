from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any

from app.services.medwood_pipeline import (
    process_material_json,
    process_material_excel
)

router = APIRouter(
    prefix="/fdif/medwood/materials",
    tags=["Medwood - Materials"]
)


# -----------------------------
# JSON INGESTION
# -----------------------------
@router.post("")
def ingest_material(body: Dict[str, Any]):
    try:
        return process_material_json(body)
    except Exception as e:
        raise HTTPException(400, str(e))


# -----------------------------
# EXCEL INGESTION
# -----------------------------
@router.post("/upload")
async def upload_materials(file: UploadFile = File(...)):
    try:
        return process_material_excel(file)
    except Exception as e:
        raise HTTPException(400, str(e))
