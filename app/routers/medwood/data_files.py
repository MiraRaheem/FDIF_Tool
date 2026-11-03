"""Generate Medwood review files and return them as ZIP downloads."""

from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
import csv
import json

from app.services.medwood_process_executions import build_process_execution_outputs
from app.services.medwood_work_orders import write_work_order_csvs
from app.services.medwood_production_ingestion import (
    build_medwood_manufactured_products,
    build_medwood_product_types,
)

router = APIRouter(
    prefix="/fdif/medwood/data-files",
    tags=["MEDWOOD Data Files"],
)


def _zip_response(files: dict[str, Path], filename: str) -> StreamingResponse:
    archive = BytesIO()
    with ZipFile(archive, mode="w", compression=ZIP_DEFLATED) as zip_file:
        for path in files.values():
            zip_file.write(path, arcname=path.name)
    archive.seek(0)
    return StreamingResponse(
        archive,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path


async def _read_transaction_uploads(files: list[UploadFile]) -> list[tuple[str, bytes]]:
    if not files:
        raise HTTPException(status_code=422, detail="Upload at least one Transactions file")
    result = []
    for upload in files:
        content = await upload.read()
        if not content:
            raise HTTPException(status_code=422, detail=f"Uploaded file '{upload.filename}' is empty")
        result.append((upload.filename or "transactions.xlsx", content))
    return result


def _prepared_records_csv(build: dict, path: Path, entity: str) -> Path:
    """Flatten prepared ontology records into reviewable mapping columns."""
    rows = []
    for record in build["records"]:
        row = {"individualName": record["individualName"]}
        for prop in record.get("dataProperties", []):
            row[prop["property"]] = prop["value"]
        for prop in record.get("objectProperties", []):
            row[prop["property"]] = prop["value"]
        rows.append(row)
    if entity == "ProductType":
        columns = ["individualName", "hasProductID"]
    else:
        columns = [
            "individualName", "hasManufacturedProductID", "hasManufacturedQuantity",
            "hasProductionDate", "isInstanceOfProductType", "isProducedByWorkOrder",
            "producedAtFactory", "isStoredIn",
        ]
    return _write_csv(path, columns, rows)


def _write_prep_metadata(path: Path, build: dict) -> Path:
    path.write_text(json.dumps({
        "entity": build["entity"],
        "summary": build["summary"],
        "warnings": build["warnings"],
        "referenceConventions": build.get("referenceConventions", {}),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


async def _generate_product_prep(files: list[UploadFile], builder, entity: str, archive_name: str):
    inputs = await _read_transaction_uploads(files)
    try:
        build = builder(inputs)
        with TemporaryDirectory(prefix=f"fdif-medwood-{entity.lower()}-") as temp_dir:
            root = Path(temp_dir)
            outputs = {
                "data": _prepared_records_csv(build, root / f"{entity.lower()}_review.csv", entity),
                "metadata": _write_prep_metadata(root / f"{entity.lower()}_preparation.json", build),
            }
            return _zip_response(outputs, archive_name)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not prepare MEDWOOD {entity} data: {exc}") from exc
    finally:
        for upload in files:
            await upload.close()


@router.post("/product-types", response_class=StreamingResponse)
async def generate_product_type_files(
    transactions_files: list[UploadFile] = File(..., description="One or more MEDWOOD Transactions XLSX/XLSB/CSV files"),
):
    """Prepare distinct article codes as ProductType IDs and download review files."""
    return await _generate_product_prep(
        transactions_files, build_medwood_product_types, "ProductType", "medwood_product_type_outputs.zip"
    )


@router.post("/manufactured-products", response_class=StreamingResponse)
async def generate_manufactured_product_files(
    transactions_files: list[UploadFile] = File(..., description="One or more MEDWOOD Transactions XLSX/XLSB/CSV files"),
):
    """Prepare ManufacturedProduct mappings from Referencia=Producción rows."""
    return await _generate_product_prep(
        transactions_files, build_medwood_manufactured_products, "ManufacturedProduct",
        "medwood_manufactured_product_outputs.zip",
    )


@router.post("/work-orders", response_class=StreamingResponse)
def generate_work_order_files(
    transactions_file: UploadFile = File(...),
    performance_file: UploadFile = File(...),
):
    """Upload source workbooks and download the three Work Order CSV reports."""
    try:
        with TemporaryDirectory(prefix="fdif-medwood-work-orders-") as temp_dir:
            root = Path(temp_dir)
            transactions_path = root / Path(transactions_file.filename or "transactions.xlsx").name
            performance_path = root / Path(performance_file.filename or "performance.xlsx").name
            transactions_path.write_bytes(transactions_file.file.read())
            performance_path.write_bytes(performance_file.file.read())
            output_dir = root / "outputs"
            outputs = write_work_order_csvs(
                output_dir=output_dir,
                transactions_path=transactions_path,
                performance_path=performance_path,
            )
            return _zip_response(outputs, "medwood_work_order_outputs.zip")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        transactions_file.file.close()
        performance_file.file.close()


@router.post("/process-executions", response_class=StreamingResponse)
def generate_process_execution_files(
    performance_file: UploadFile = File(...),
    work_orders_file: UploadFile | None = File(default=None),
):
    """Upload a performance workbook and download the three ProcessExecution reports.

    Optionally include the generated Work Order review CSV to cross-check
    ProcessExecution references against known Work Order IDs.
    """
    try:
        with TemporaryDirectory(prefix="fdif-medwood-process-executions-") as temp_dir:
            root = Path(temp_dir)
            performance_path = root / Path(performance_file.filename or "performance.xlsx").name
            performance_path.write_bytes(performance_file.file.read())
            work_orders_path = None
            if work_orders_file is not None:
                work_orders_path = root / Path(work_orders_file.filename or "work_orders.csv").name
                work_orders_path.write_bytes(work_orders_file.file.read())
            output_dir = root / "outputs"
            outputs = build_process_execution_outputs(
                performance_path=performance_path,
                output_dir=output_dir,
                work_orders_path=work_orders_path,
            )
            return _zip_response(outputs, "medwood_process_execution_outputs.zip")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        performance_file.file.close()
        if work_orders_file is not None:
            work_orders_file.file.close()
