from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any

from app.services.budatec_pipeline import process_customer_json, process_customer_excel

router = APIRouter(
    prefix="/fdif/budatec/customers",
    tags=["Budatec - Customers"]
)


@router.post(
    "",
    summary="Ingest a single customer (JSON)",
    description="""
Create or update a customer from ERP JSON data.

Pipeline:
ERP → Canonical → Validation → Ontology
"""
)
def ingest_customer(body: Dict[str, Any]):

    try:
        return process_customer_json(body)

    except Exception as e:
        raise HTTPException(400, str(e))


@router.post(
    "/upload",
    summary="Bulk upload customers (Excel)",
    description="""
Upload Excel file containing customers.

Each row is:
- cleaned
- normalized
- validated
- inserted into ontology
"""
)
async def upload_customers(file: UploadFile = File(...)):

    try:
        return process_customer_excel(file)

    except Exception as e:
        raise HTTPException(400, str(e))
