"""Upload reviewed MEDWOOD CSVs and create or update NARRATE individuals."""

from fastapi import APIRouter, File, HTTPException, UploadFile

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
    """Create or update WorkOrders using the reviewed Work Order CSV."""
    return await _upload_and_ingest(file, ingest_work_orders)


@router.post("/process-executions")
async def ingest_process_execution_review(file: UploadFile = File(..., description="medwood_process_executions_review.csv")):
    """Create or update ProcessExecutions and link them to existing WorkOrders."""
    return await _upload_and_ingest(file, ingest_process_executions)


@router.post("/manufactured-products")
async def ingest_manufactured_product_review(file: UploadFile = File(..., description="manufacturedproduct_review.csv")):
    """Create or update ManufacturedProducts and synchronize inverse links."""
    return await _upload_and_ingest(file, ingest_manufactured_products)
