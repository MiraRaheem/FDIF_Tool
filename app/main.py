from fastapi import FastAPI
from app.routers import (
    ingest_router,
    harmonize_router,
    validate_router,
    iot_router,
    work_order_router,
    blueprint_router, medwood
)

api = FastAPI(
    title="FDIF PoC",
    version="0.1.0",
    description="Federated Data Integration Framework prototype"
)

# ---- medwood pipeline ----
api.include_router(medwood.router, prefix="/fdif")
# ---- FDIF pipeline ----
api.include_router(ingest_router, prefix="/fdif")
api.include_router(harmonize_router, prefix="/fdif")
api.include_router(validate_router, prefix="/fdif")

# ---- Domain / demo routes ----
api.include_router(iot_router, prefix="/fdif")
api.include_router(work_order_router, prefix="/fdif")
api.include_router(blueprint_router, prefix="/fdif")

@api.get("/")
def home():
    return {"message": "FDIF API is running 🚀"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:api", host="127.0.0.1", port=8000, reload=True)
