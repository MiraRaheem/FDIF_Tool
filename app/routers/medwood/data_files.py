"""Generate Medwood review files and return them as ZIP downloads."""

from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile
from collections import Counter
from datetime import date, datetime
import hashlib
import re
import unicodedata

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
import csv
import json
import pandas as pd

from app.services.medwood_process_executions import build_process_execution_outputs
from app.services.medwood_work_orders import write_work_order_csvs

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


async def _generate_product_prep(files: list[UploadFile], entity: str, archive_name: str):
    inputs = await _read_transaction_uploads(files)
    try:
        build = _prepare_product_types(inputs) if entity == "ProductType" else _prepare_manufactured_products(inputs)
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


def _norm(value) -> str:
    text = "" if pd.isna(value) else str(value).strip()
    return "".join(char for char in unicodedata.normalize("NFKD", text).casefold() if not unicodedata.combining(char))


def _clean(value):
    if pd.isna(value):
        return None
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    text = str(value).strip()
    if not text or text.casefold() in {"nan", "none", "nat"}:
        return None
    return re.sub(r"^(\-?\d+)\.0+$", r"\1", text)


def _local_name(prefix: str, value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", f"{prefix}_{value}").strip("_")
    return safe[:180] or prefix


def _transaction_frames(files: list[tuple[str, bytes]], required: set[str]):
    frames = []
    warnings = []
    for filename, content in files:
        suffix = Path(filename).suffix.lower()
        if suffix == ".csv":
            workbook_frames = [pd.read_csv(BytesIO(content), dtype=object)]
        elif suffix in {".xlsx", ".xlsm", ".xlsb"}:
            engine = "pyxlsb" if suffix == ".xlsb" else "openpyxl"
            workbook = pd.ExcelFile(BytesIO(content), engine=engine)
            workbook_frames = []
            for sheet in workbook.sheet_names:
                if _norm(sheet) == "tabla" and len(workbook.sheet_names) > 1:
                    continue
                workbook_frames.append(pd.read_excel(workbook, sheet_name=sheet, dtype=object))
        else:
            raise ValueError(f"{filename}: unsupported file type {suffix or '(no extension)'}")
        matching = []
        for frame in workbook_frames:
            frame.columns = [str(column).strip() for column in frame.columns]
            if required.issubset(frame.columns):
                matching.append(frame)
        if not matching:
            warnings.append(f"{filename}: no sheet contained required columns: {', '.join(sorted(required))}")
        frames.extend(matching)
    if not frames:
        raise ValueError(f"No Transactions sheet contained required columns: {', '.join(sorted(required))}")
    combined = pd.concat(frames, ignore_index=True, sort=False)
    production = combined[combined["Referencia"].map(_norm).eq("produccion")].copy()
    if production.empty:
        warnings.append("No transaction rows matched Referencia = 'Producción'.")
    return production, warnings


def _property(name: str, value) -> dict:
    return {"property": name, "value": str(value)}


def _prepare_product_types(files: list[tuple[str, bytes]]) -> dict:
    production, warnings = _transaction_frames(files, {"Código de artículo", "Referencia"})
    codes = sorted({code for code in production["Código de artículo"].map(_clean) if code})
    records = [{
        "individualName": _local_name("ProductType", code),
        "dataProperties": [_property("hasProductID", code)],
        "objectProperties": [],
    } for code in codes]
    return {"entity": "ProductType", "summary": {"productionTransactionRows": len(production), "distinctArticleCodes": len(records)}, "warnings": warnings, "records": records}


def _prepare_manufactured_products(files: list[tuple[str, bytes]]) -> dict:
    required = {"Código de artículo", "Número", "Referencia", "Cantidad", "Fecha física", "Sitio", "Almacén"}
    production, warnings = _transaction_frames(files, required)
    records = []
    occurrences = Counter()
    for _, row in production.iterrows():
        values = {column: None if pd.isna(row[column]) else str(row[column]) for column in sorted(required)}
        digest = hashlib.sha256(json.dumps(values, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]
        occurrences[digest] += 1
        name = f"MEDWOOD_ManufacturedProduct_{digest}_{occurrences[digest]}"
        data = [_property("hasManufacturedProductID", name)]
        quantity = _clean(row["Cantidad"])
        if quantity is not None:
            try:
                quantity = str(float(quantity.replace(",", ".")))
            except ValueError:
                pass
            data.append(_property("hasManufacturedQuantity", quantity))
        raw_date = row["Fecha física"]
        if not pd.isna(raw_date):
            if isinstance(raw_date, (date, datetime, pd.Timestamp)):
                production_date = raw_date.date().isoformat() if isinstance(raw_date, (datetime, pd.Timestamp)) else raw_date.isoformat()
            else:
                parsed = pd.to_datetime(raw_date, errors="coerce", dayfirst=True)
                production_date = None if pd.isna(parsed) else parsed.date().isoformat()
            if production_date:
                data.append(_property("hasProductionDate", production_date))
        objects = []
        article, order = _clean(row["Código de artículo"]), _clean(row["Número"])
        site, warehouse = _clean(row["Sitio"]), _clean(row["Almacén"])
        if article:
            objects.append(_property("isInstanceOfProductType", _local_name("ProductType", article)))
        if order:
            objects.append(_property("isProducedByWorkOrder", _local_name("MEDWOOD_WorkOrder", order)))
        if site:
            objects.append(_property("producedAtFactory", "MEDWOOD_Factory" if _norm(site) == "mc" else _local_name("MEDWOOD_Factory", site)))
        if warehouse and _norm(warehouse) not in {"none", "null", "n/a", "na"}:
            objects.append(_property("isStoredIn", _local_name("MEDWOOD_Warehousing", warehouse.upper())))
        records.append({"individualName": name, "dataProperties": data, "objectProperties": objects})
    return {"entity": "ManufacturedProduct", "summary": {"productionTransactionRows": len(production), "manufacturedProductsPrepared": len(records)}, "warnings": warnings, "records": records}


@router.post("/product-types", response_class=StreamingResponse)
async def generate_product_type_files(
    transactions_file: UploadFile = File(..., description="MEDWOOD Transactions XLSX/XLSB/CSV file"),
):
    """Prepare distinct article codes as ProductType IDs and download review files."""
    return await _generate_product_prep(
        [transactions_file], "ProductType", "medwood_product_type_outputs.zip"
    )


@router.post("/manufactured-products", response_class=StreamingResponse)
async def generate_manufactured_product_files(
    transactions_file: UploadFile = File(..., description="MEDWOOD Transactions XLSX/XLSB/CSV file"),
):
    """Prepare ManufacturedProduct mappings from Referencia=Producción rows."""
    return await _generate_product_prep(
        [transactions_file], "ManufacturedProduct",
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
