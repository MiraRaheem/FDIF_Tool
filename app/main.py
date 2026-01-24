from fastapi import FastAPI
from app.routers import ingest, validate, blueprint, iot
from app.routers import (
ingest_router,
harmonize_router,
validate_router,
iot_router
)

api = FastAPI(
    title="FDIF PoC",
    version="0.1.0",
    description="Federated Data Integration Framework prototype"
)

app.include_router(ingest_router, prefix="/fdif")
app.include_router(harmonize_router, prefix="/fdif")
app.include_router(validate_router, prefix="/fdif")
app.include_router(iot_router, prefix="/fdif")
api.include_router(ingest.router, prefix="/fdif")
app.include_router(harmonize.router, prefix="/fdif")
api.include_router(validate.router, prefix="/fdif")
api.include_router(blueprint.router, prefix="/fdif")
api.include_router(iot.router, prefix="/fdif")
api.include_router(ingest.router, prefix="/fdif")
@api.get("/")
def home():
    return {"message": "FDIF API is running 🚀"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:api", host="127.0.0.1", port=8000, reload=True)
