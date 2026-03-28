from fastapi import FastAPI

from app.routers import medwood
from app.routers import budatec   # ← your new router

api = FastAPI(
    title="FDIF PoC",
    version="0.1.0"
)

api.include_router(medwood, prefix="/fdif")
api.include_router(budatec, prefix="/fdif")

@api.get("/")
def home():
    return {"message": "FDIF API is running 🚀"}
