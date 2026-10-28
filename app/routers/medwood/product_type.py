from fastapi import APIRouter, File, HTTPException, UploadFile
from typing import Dict, Any

from app.services.medwood_pipeline import (
    process_product_type_json,
    process_product_type_ids_excel,
)

router = APIRouter(
    prefix="/fdif/medwood/product-types",
    tags=["Medwood - Product Types"]
)


@router.post("")
def ingest_product_type(body: Dict[str, Any]):
    try:
        return process_product_type_json(body)

    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/upload-ids")
def upload_product_type_ids(file: UploadFile = File(...)):
    """Create minimal ProductType instances from an Excel product_code column."""
    try:
        return process_product_type_ids_excel(file)
    except Exception as e:
        raise HTTPException(400, str(e))
    finally:
        file.file.close()
