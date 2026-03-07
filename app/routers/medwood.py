from app.services.medwood_blueprint_mapper import supplier_to_blueprint
from app.services.blueprint_api import create_blueprint_instance
from fastapi import APIRouter, UploadFile, File, Query
from app.services.validator import validate_supplier
import pandas as pd

from app.services.medwood_registry import get_harmonizer

router = APIRouter(tags=["medwood"])


@router.post("/medwood/upload")
async def upload_medwood_dataset(
    dataset: str = Query(...),
    file: UploadFile = File(...)
):

    df = pd.read_excel(file.file)

    rows = df.to_dict(orient="records")

    harmonizer = get_harmonizer(dataset)

    canonical_rows = []

    results = []

for row in rows:

    canonical = harmonizer(row)
    validated = validate_supplier(canonical)

    if dataset == "supplierAccounts":

        blueprint_payload = supplier_to_blueprint(validated)

        response = create_blueprint_instance(
            "MaterialSupplier",
            blueprint_payload
        )

        results.append({
            "canonical": canonical,
            "blueprint_response": response
        })
    return {
    "dataset": dataset,
    "rows_processed": len(results),
    "sample": results[:3]}
