from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any

from app.services.medwood_pipeline import (
    process_medwood_supplier_json,
    process_medwood_supplier_excel
)

router = APIRouter(
    prefix="/fdif/medwood/suppliers",
    tags=["Medwood - Suppliers"]
)


@router.post("")
def ingest_supplier(body: Dict[str, Any]):
    try:
        return process_medwood_supplier_json(body)
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/upload")
async def upload_suppliers(file: UploadFile = File(...)):
    try:
        return process_medwood_supplier_excel(file)
    except Exception as e:
        raise HTTPException(400, str(e))
