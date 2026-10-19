
from fastapi import APIRouter

from app.routers.budatech_v2.customer import router as customer_router
from app.routers.budatech_v2.supplier import router as supplier_router


router = APIRouter()
router.include_router(customer_router)
router.include_router(supplier_router)
