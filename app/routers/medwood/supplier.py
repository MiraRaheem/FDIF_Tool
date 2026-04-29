from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any

from app.services.medwood_pipeline import (
    process_medwood_supplier_json,
    process_medwood_supplier_excel,
    process_supplier_performance_json,
    process_supplier_performance_excel
)

router = APIRouter(
    prefix="/fdif/medwood/suppliers",
    tags=["Medwood - Suppliers"]
)

# -----------------------------
# SUPPLIER (MASTER DATA)
# -----------------------------

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


# -----------------------------
# SUPPLIER PERFORMANCE
# -----------------------------

@router.post("/performance")
def ingest_supplier_performance(body: Dict[str, Any]):
    try:
        return process_supplier_performance_json(body)
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/performance/upload")
async def upload_supplier_performance(file: UploadFile = File(...)):
    try:
        return process_supplier_performance_excel(file)
    except Exception as e:
        raise HTTPException(400, str(e))
