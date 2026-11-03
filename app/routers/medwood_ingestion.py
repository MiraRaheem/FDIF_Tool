"""MEDWOOD-specific ingestion endpoints.

All routes default to preview mode. Add ?commit=true to write mapped instances
through NARRATE's AddIndividualServlet2 endpoint (requires NARRATE_BASE_URL).
"""
from typing import List, Tuple

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.services.medwood_production_ingestion import (
    build_medwood_records,
    build_medwood_product_types,
    build_medwood_manufactured_products,
    commit_records,
)

router = APIRouter(prefix="/medwood", tags=["MEDWOOD ingestion"])


async def _read_uploads(files: List[UploadFile], label: str) -> List[Tuple[str, bytes]]:
    if not files:
        raise HTTPException(status_code=422, detail=f"Upload at least one {label} file")
    result = []
    for upload in files:
        content = await upload.read()
        if not content:
            raise HTTPException(status_code=422, detail=f"Uploaded file '{upload.filename}' is empty")
        result.append((upload.filename or f"{label}.xlsx", content))
    return result


async def _build(transactions_files: List[UploadFile], performance_files: List[UploadFile]):
    transaction_bytes = await _read_uploads(transactions_files, "transaction")
    performance_bytes = await _read_uploads(performance_files, "performance")
    try:
        return build_medwood_records(transaction_bytes, performance_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read MEDWOOD files: {exc}") from exc


async def _prepare_transactions(files: List[UploadFile], builder):
    transaction_bytes = await _read_uploads(files, "transaction")
    try:
        return builder(transaction_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not prepare MEDWOOD transaction data: {exc}") from exc


def _preview_response(build, selected_class: str = "all"):
    all_records = {
        "WorkOrder": build.work_orders,
        "ProductionProcess": build.production_processes,
        "ProcessExecution": build.process_executions,
    }
    if selected_class == "all":
        chosen = all_records
    else:
        chosen = {selected_class: all_records[selected_class]}
    return {
        "mode": "preview_only",
        "summary": build.summary,
        "selectedClassCounts": {name: len(records) for name, records in chosen.items()},
        "samplePayloads": {name: records[:3] for name, records in chosen.items()},
        "warnings": build.warnings,
        "mappingNotes": [
            "WorkOrder.hasWorkOrderID <- Transactions.Número, joined to Performance.Producción; only Reference/Referencia='Producción' transactions are considered.",
            "WorkOrder.hasRequestedQuantity <- maximum numeric Performance.Nº Piezas Teórico per work order; conflicts are reported as warnings.",
            "ProductionProcess.hasProcessID <- Performance.Trabajo; hasProcessName uses Recurso when available, otherwise the most common Centro de Trabajo label.",
            "ProcessExecution is aggregated per (Performance.Producción, Performance.Trabajo); actual machine hours are converted to minutes; output and defects are summed.",
            "No planned WorkOrder dates or execution start/end timestamps are generated because MEDWOOD does not manage them explicitly.",
        ],
    }


@router.post("/prepare/product-types")
async def prepare_product_types(
    transactions_files: List[UploadFile] = File(
        ..., description="One or more MEDWOOD Transactions XLSX/XLSB/CSV files"
    ),
):
    """Prepare distinct ProductType identifiers from production transactions only."""
    return await _prepare_transactions(transactions_files, build_medwood_product_types)


@router.post("/prepare/manufactured-products")
async def prepare_manufactured_products(
    transactions_files: List[UploadFile] = File(
        ..., description="One or more MEDWOOD Transactions XLSX/XLSB/CSV files"
    ),
):
    """Prepare ManufacturedProduct payloads from rows where Referencia is Producción."""
    return await _prepare_transactions(transactions_files, build_medwood_manufactured_products)


@router.post("/preview")
async def preview_medwood(
    transactions_files: List[UploadFile] = File(..., description="One or more MEDWOOD Transactions XLSX/XLSB/CSV files"),
    performance_files: List[UploadFile] = File(..., description="One or more MEDWOOD Performance XLSX/XLSB/CSV files"),
):
    """Parse both sources and preview all three classes without writing to NARRATE."""
    build = await _build(transactions_files, performance_files)
    return _preview_response(build)


@router.post("/ingest/work-orders")
async def ingest_work_orders(
    transactions_files: List[UploadFile] = File(...),
    performance_files: List[UploadFile] = File(...),
    commit: bool = Query(False, description="Set true to create records in NARRATE; otherwise preview only"),
):
    build = await _build(transactions_files, performance_files)
    if not commit:
        return _preview_response(build, "WorkOrder")
    try:
        result = commit_records(build.work_orders)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"mode": "committed", "summary": build.summary, "result": result, "warnings": build.warnings}


@router.post("/ingest/production-processes")
async def ingest_production_processes(
    transactions_files: List[UploadFile] = File(...),
    performance_files: List[UploadFile] = File(...),
    commit: bool = Query(False, description="Set true to create records in NARRATE; otherwise preview only"),
):
    build = await _build(transactions_files, performance_files)
    if not commit:
        return _preview_response(build, "ProductionProcess")
    try:
        result = commit_records(build.production_processes)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"mode": "committed", "summary": build.summary, "result": result, "warnings": build.warnings}


@router.post("/ingest/process-executions")
async def ingest_process_executions(
    transactions_files: List[UploadFile] = File(...),
    performance_files: List[UploadFile] = File(...),
    commit: bool = Query(False, description="Set true to create records in NARRATE; otherwise preview only"),
):
    build = await _build(transactions_files, performance_files)
    if not commit:
        return _preview_response(build, "ProcessExecution")
    try:
        result = commit_records(build.process_executions)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"mode": "committed", "summary": build.summary, "result": result, "warnings": build.warnings}


@router.post("/ingest/all")
async def ingest_all_medwood(
    transactions_files: List[UploadFile] = File(...),
    performance_files: List[UploadFile] = File(...),
    commit: bool = Query(False, description="Set true to create records in NARRATE; otherwise preview only"),
):
    """Preview or ingest all classes in dependency order: process, work order, execution."""
    build = await _build(transactions_files, performance_files)
    if not commit:
        return _preview_response(build)
    try:
        # Keep this order: executions reference both work orders and processes.
        process_result = commit_records(build.production_processes)
        work_order_result = commit_records(build.work_orders)
        execution_result = commit_records(build.process_executions)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "mode": "committed",
        "summary": build.summary,
        "ingestionOrder": ["ProductionProcess", "WorkOrder", "ProcessExecution"],
        "results": {
            "ProductionProcess": process_result,
            "WorkOrder": work_order_result,
            "ProcessExecution": execution_result,
        },
        "warnings": build.warnings,
    }
