from fastapi import APIRouter, UploadFile, File, Query
from app.services.validator import validate_supplier_performance
from app.services.blueprint_adapter import add_supplier_performance
import pandas as pd

from app.services.medwood_registry import get_harmonizer
from app.services.validator import validate_supplier
from app.services.blueprint_adapter import create_supplier_instance

router = APIRouter(tags=["medwood"])


@router.post("/medwood/upload")
async def upload_medwood_dataset(
    dataset: str = Query(...),
    file: UploadFile = File(...)
):

    df = pd.read_excel(file.file)

    rows = df.to_dict(orient="records")

    harmonizer = get_harmonizer(dataset)

    results = []

    for row in rows:

    canonical = harmonizer(row)

    if dataset == "supplierAccounts":

        validated = validate_supplier(canonical)

        result = create_supplier_instance(validated)

    elif dataset == "supplierPerformance":

        validated = validate_supplier_performance(canonical)

        result = add_supplier_performance(validated)

    results.append({
        "canonical": canonical,
        "blueprint_response": result
    })
    
    return {
        "dataset": dataset,
        "rows_processed": len(results),
        "sample": results[:3]
    }
