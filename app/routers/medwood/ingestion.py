"""Upload reviewed MEDWOOD CSVs and create or update NARRATE individuals."""

from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.services.medwood_review_ingestion import (
    ingest_manufactured_products,
    ingest_process_executions,
    ingest_product_types,
    ingest_work_orders,
)

router = APIRouter(
    prefix="/fdif/medwood/ingest",
    tags=["MEDWOOD Ingestion"],
)


class IngestionReport(BaseModel):
    """Stable JSON response schema so Swagger can render upload feedback."""

    status: str
    entity: str
    summary: dict[str, int]
    ingested: list[dict[str, Any]] = Field(default_factory=list)
    rejectedRecords: list[dict[str, Any]] = Field(default_factory=list)
    failedRecords: list[dict[str, Any]] = Field(default_factory=list)
    relationshipFailures: list[dict[str, Any]] = Field(default_factory=list)
    recordWarnings: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    class Config:
        extra = "allow"


async def _upload_and_ingest(file: UploadFile, processor):
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=422, detail="Uploaded CSV is empty")
        return processor(content)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    finally:
        await file.close()


@router.post("/product-types")
async def ingest_product_type_review(file: UploadFile = File(..., description="producttype_review.csv")):
    """Create or update ProductTypes using the reviewed ProductType CSV."""
    return await _upload_and_ingest(file, ingest_product_types)


@router.post("/work-orders")
async def ingest_work_order_review(file: UploadFile = File(..., description="work_orders_review.csv")):
    """Create or update WorkOrders from the reviewed CSV.

    Maps the order ID and requested quantity, maps
    unvalidatedSumPiezasBuenasAcrossPerformanceRows to hasCompletedQuantity,
    and normalizes common actual start/end date formats to xsd:dateTime; date-only
    values become midnight. Ambiguous slash dates are interpreted month/day/year
    to match the reviewed export. The completed quantity is an unvalidated sum across performance
    rows and may double-count pieces reported at multiple stations; review it
    before treating it as authoritative. appliesToProduct and includesExecution
    are linked later when ManufacturedProduct and ProcessExecution records are
    ingested, respectively.
    """
    return await _upload_and_ingest(file, ingest_work_orders)


@router.post("/process-executions")
async def ingest_process_execution_review(
    file: UploadFile = File(..., description="medwood_process_executions_review.csv"),
) -> IngestionReport:
    """Create/update ProcessExecutions with reviewed dates, duration, quantities, status, and WorkOrder link.

    Date-only candidates are stored as midnight UTC to satisfy xsd:dateTimeStamp;
    this is a storage convention, not an observed clock time. Duration/output/
    defect candidates are row sums and should be reviewed for additivity. A work
    centre label is not linked to usesMachineInstance unless a matching Machine
    individual is available.
    """
    return await _upload_and_ingest(file, ingest_process_executions)


@router.post("/manufactured-products", response_model=IngestionReport)
async def ingest_manufactured_product_review(
    file: UploadFile = File(..., description="manufacturedproduct_review.csv"),
) -> IngestionReport:
    """Create/update transaction-row ManufacturedProducts with reviewed data and inverse links.

    Maps the manufactured ID, integer quantity, normalized production date,
    ProductType, WorkOrder, Factory, and optional Warehouse relationships.
    Returns per-row data and the status of each direct and inverse relationship.
    """
    return await _upload_and_ingest(file, ingest_manufactured_products)
