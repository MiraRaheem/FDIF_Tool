from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any

from app.services.budatec_pipeline import process_supplier_json, process_supplier_excel

router = APIRouter(
    prefix="/fdif/budatec/suppliers",
    tags=["Budatec - Suppliers"]
)


@router.post(
    "",
    summary="Ingest a single supplier (JSON)",
    description="""
Create or update a supplier from ERP JSON data.

Steps:
1. Normalize ERP fields
2. Harmonize into canonical model
3. Validate business rules
4. Insert into ontology (Blueprint)

Expected body:
{
  "data": { ... ERP supplier object ... }
}
"""
)
def ingest_supplier(body: Dict[str, Any]):

    try:
        return process_supplier_json(body)

    except Exception as e:
        raise HTTPException(400, str(e))


@router.post(
    "/upload",
    summary="Bulk upload suppliers (Excel)",
    description="""
Upload an ERP Excel file containing suppliers.

System will:
- Detect header row automatically
- Extract rows
- Process each row independently
- Return partial success if some rows fail
"""
)
async def upload_suppliers(file: UploadFile = File(...)):

    try:
        return process_supplier_excel(file)

    except Exception as e:
        raise HTTPException(400, str(e))
